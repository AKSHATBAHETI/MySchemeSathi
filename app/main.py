# ===============================
# GLOBAL STATE
# ===============================

chat_memory = {}
last_shown_schemes: dict[str, list[dict]] = {}

# ===============================
# HELPER FUNCTIONS
# ===============================

def clear_chat_data(chat_id: str):
    """Clear all stored data for a chat (for fresh starts)."""
    if chat_id in chat_memory:
        del chat_memory[chat_id]
    if chat_id in last_shown_schemes:
        del last_shown_schemes[chat_id]
    from app.user_profile import clear_profile
    clear_profile(chat_id)
    print(f"[CHAT CLEARED] Cleared all data for chat {chat_id}")

# ===============================
# IMPORTS
# ===============================

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from app.config import TELEGRAM_BOT_TOKEN, GROQ_API_KEY, SCHEME_JSON_PATH
from app.schemes_service import (
    get_eligible_schemes_using_ai,
    search_schemes,
    search_schemes_as_list,
    get_all_schemes
)
from app.pdf_generator import generate_schemes_pdf
from app.user_profile import get_or_create_profile

import traceback
import re
import os
import json

# ===============================
# SAFETY CONSTANTS
# ===============================

MAX_MESSAGES = 6
MAX_CONTEXT_CHARS = 1500
MAX_SCHEME_CHARS = 800

# ===============================
# LLM INITIALIZATION
# ===============================

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0
)

# ===============================
# UTILITY FUNCTIONS
# ===============================

def safe_truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    return text[-limit:]

# ===============================
# PROFILE EXTRACTION
# ===============================

import re

# Keywords and patterns for profile extraction
STATES = ["delhi", "maharashtra", "karnataka", "tamil nadu", "uttar pradesh", "west bengal", 
          "punjab", "haryana", "telangana", "rajasthan", "bihar", "odisha", "madhya pradesh",
          "andhra pradesh", "gujarat", "himachal pradesh", "jharkhand", "goa", "kerala", 
          "tripura", "manipur", "meghalaya", "assam", "arunachal pradesh"]

AGE_PATTERN = r'(\d{1,3})\s*(?:year|yr|years|yrs|old)'
AGE_PATTERN = r'(?:age|years?|yrs?|old)[\s:]*(\d{1,3})|(\d{1,3})\s*(?:year|yr|years|yrs|old)'

async def extract_user_info_from_text(text: str, profile) -> None:
    """Extract user profile info using both pattern matching and AI."""
    text_lower = text.lower()
    
    # Pattern-based extraction (fast)
    print(f"[EXTRACTION] Parsing user text: {text[:50]}...")
    
    # Age extraction - improved to catch "age is 20", "20 years old", etc.
    age_match = re.search(AGE_PATTERN, text_lower)
    if age_match:
        # Get the age from either group 1 or group 2
        age_str = age_match.group(1) or age_match.group(2)
        if age_str:
            age = int(age_str)
            profile.add_info("age", age)
            print(f"[EXTRACTION] Found age: {age}")
    
    # State extraction
    for state in STATES:
        if state in text_lower:
            profile.add_info("state", state.title())
            print(f"[EXTRACTION] Found state: {state.title()}")
            break
    
    # Gender extraction - normalize all gender keywords
    male_keywords = ["male", "man", "boy", "mr.", "he", "i am a male", "i'm male", "i am male"]
    female_keywords = ["female", "woman", "girl", "mrs.", "ms.", "she", "i am a female", "i'm female", "i am female", "i am a woman", "i'm a woman"]
    
    found_gender = None
    for keyword in male_keywords:
        if keyword in text_lower:
            found_gender = "Male"
            break
    
    if not found_gender:
        for keyword in female_keywords:
            if keyword in text_lower:
                found_gender = "Female"
                break
    
    if found_gender:
        profile.add_info("gender", found_gender)
        print(f"[EXTRACTION] Found gender: {found_gender}")
    
    # Occupation keywords
    occupations = ["student", "farmer", "businessman", "employee", "doctor", "engineer", 
                   "teacher", "nurse", "laborer", "self-employed", "unemployed", "retired"]
    for occ in occupations:
        if occ in text_lower:
            profile.add_info("occupation", occ.title())
            print(f"[EXTRACTION] Found occupation: {occ.title()}")
            break
    
    # Disability keywords
    if any(word in text_lower for word in ["disabled", "disability", "pwd", "physically challenged"]):
        profile.add_info("disability", "Yes")
        print(f"[EXTRACTION] Found disability: Yes")
    
    # Income/poverty keywords
    if any(word in text_lower for word in ["poor", "low income", "below poverty", "bpl"]):
        profile.add_info("family_income", "Low")
        print(f"[EXTRACTION] Found income: Low")
    elif any(word in text_lower for word in ["middle class", "medium income", "stable income"]):
        profile.add_info("family_income", "Medium")
        print(f"[EXTRACTION] Found income: Medium")
    
    # Store raw text
    profile.add_raw_text(text)

# ===============================
# SIMPLE MESSAGE CHECK
# ===============================

async def is_greeting_or_simple_message(text: str) -> bool:
    greetings = {
        "hi", "hello", "hey", "hii",
        "thanks", "thank you",
        "ok", "okay", "yes", "no"
    }
    text = text.lower().strip()
    words = text.split()
    return len(words) <= 2 and any(g in text for g in greetings)

# ===============================
# NATURAL RESPONSE
# ===============================

async def generate_natural_response(text, profile, chat_history) -> str:
    prompt = f"""
You are a friendly Indian government schemes assistant.

User profile:
{profile.get_profile_summary()}

Recent conversation:
{safe_truncate(chat_history, 500)}

User said:
{text}

Respond naturally in 1–2 sentences.
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content

# ===============================
# INTENT DETECTION
# ===============================

async def detect_intent(text: str) -> str:
    text_lower = text.lower().strip()
    
    # Check for greeting first (exact matches are safer)
    greetings = {"hi", "hello", "hey", "hii", "thanks", "thank you", "ok", "okay", "yes", "no"}
    if text_lower in greetings:
        return "greeting"
    
    # Check for specific requests
    if any(w in text_lower for w in ["pdf", "download"]):
        return "pdf_request"
    if any(w in text_lower for w in ["eligible", "eligibility", "which scheme"]):
        return "eligibility_query"
    
    # Everything else is a general query (search/information)
    return "general_query"

# ===============================
# MAIN MESSAGE HANDLER
# ===============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text
        chat_id = str(update.effective_chat.id)

        print(f"\n{'='*60}")
        print(f"[USER {chat_id}] {user_text}")
        print(f"{'='*60}")

        # ---------------------------
        # CHAT MEMORY
        # ---------------------------

        chat_memory.setdefault(chat_id, []).append(user_text)
        recent_messages = chat_memory[chat_id][-MAX_MESSAGES:]
        full_chat_context = safe_truncate(" ".join(recent_messages), MAX_CONTEXT_CHARS)

        # ---------------------------
        # USER PROFILE
        # ---------------------------

        user_profile = get_or_create_profile(chat_id)
        await extract_user_info_from_text(user_text, user_profile)

        # ---------------------------
        # INTENT
        # ---------------------------

        intent = await detect_intent(user_text)
        print(f"[INTENT] {intent}")

        # ---------------------------
        # GREETING / SIMPLE
        # ---------------------------

        if intent == "greeting":
            print(f"[HANDLER] Treating as greeting")
            reply = await generate_natural_response(
                user_text, user_profile, full_chat_context
            )
            await update.message.reply_text(reply)
            return

        # ---------------------------
        # NUMBER SELECTION
        # ---------------------------

        m = re.search(r"\d+", user_text)
        if m and chat_id in last_shown_schemes:
            idx = int(m.group()) - 1
            schemes = last_shown_schemes[chat_id]
            if 0 <= idx < len(schemes):
                s = schemes[idx]
                await update.message.reply_text(
                    f"{s['scheme_name']}\n\n{s.get('objective','')}\n\nURL: {s.get('source_url','')}"
                )
                return

        # ---------------------------
        # PDF REQUEST
        # ---------------------------

        if intent == "pdf_request":
            print(f"[HANDLER] PDF request")
            safe_context = safe_truncate(full_chat_context, 1000)

            schemes_list = get_eligible_schemes_using_ai(
                safe_context
            )
            
            print(f"[PDF] Found {len(schemes_list)} eligible schemes")

            if not schemes_list:
                clarification = """
I need a bit more information like your age, income, state,
and occupation to generate your scheme PDF.
"""
                resp = await llm.ainvoke([HumanMessage(content=clarification)])
                await update.message.reply_text(resp.content)
                return

            pdf_path = f"eligible_schemes_{chat_id}.pdf"

            generate_schemes_pdf(
                schemes_list,
                pdf_path,
                user_profile.get_profile_summary()
            )

            with open(pdf_path, "rb") as f:
                await update.message.reply_document(f, filename="eligible_schemes.pdf")

            os.remove(pdf_path)
            return

        # ---------------------------
        # ELIGIBILITY QUERY
        # ---------------------------

        if intent == "eligibility_query":
            print(f"[HANDLER] Eligibility query")
            
            # Check if user has provided enough info
            profile_data = user_profile.get_profile()
            has_age = profile_data.get("age") is not None
            has_state = profile_data.get("state") is not None
            has_occupation = profile_data.get("occupation") is not None
            
            print(f"[ELIGIBILITY] Profile: age={has_age}, state={has_state}, occupation={has_occupation}")
            
            # If missing key info, ask user to provide
            if not (has_age and has_state):
                missing = []
                if not has_age:
                    missing.append("age")
                if not has_state:
                    missing.append("state/region")
                if not has_occupation:
                    missing.append("occupation")
                
                msg = f"To find eligible schemes, I need your: {', '.join(missing)}.\n\nPlease share these details."
                print(f"[ELIGIBILITY] Asking for: {missing}")
                await update.message.reply_text(msg)
                return
            
            # User has provided enough info, get eligible schemes
            print(f"[ELIGIBILITY] User profile sufficient. Checking eligibility...")
            profile_summary = user_profile.get_profile_summary()
            print(f"[ELIGIBILITY] Profile summary:\n{profile_summary}")
            
            schemes_list = get_eligible_schemes_using_ai(profile_summary)
            
            print(f"[ELIGIBILITY] Found {len(schemes_list)} eligible schemes")

            if not schemes_list:
                await update.message.reply_text(
                    f"Based on your profile (age {profile_data.get('age')}, {profile_data.get('state')}), "
                    "I couldn't find exactly matching schemes. However, I recommend checking the official "
                    "government website for more options that might suit your profile."
                )
                return

            msg = "Based on your profile, here are eligible schemes:\n\n"
            for i, s in enumerate(schemes_list[:5], 1):
                msg += f"{i}. {s.get('scheme_name', 'Unknown Scheme')}\n"

            msg += "\nReply 'pdf' to download."
            await update.message.reply_text(msg)
            return

        # ---------------------------
        # GENERAL QUERY
        # ---------------------------

        print(f"[HANDLER] General query - searching for schemes")
        
        # Clear old search results for this user
        if chat_id in last_shown_schemes:
            del last_shown_schemes[chat_id]
            print(f"[SEARCH] Cleared old results for user {chat_id}")
        
        # Search using ONLY the current user message, not full context
        schemes_info = search_schemes(user_text)
        schemes_info = safe_truncate(schemes_info, MAX_SCHEME_CHARS)
        
        print(f"[SEARCH] Results:\n{schemes_info[:200]}...")

        matched = search_schemes_as_list(user_text)
        print(f"[SEARCH] Matched {len(matched)} schemes")
        
        if matched:
            last_shown_schemes[chat_id] = [
                {
                    "scheme_name": s.get("scheme_name"),
                    "source_url": s.get("source_url"),
                    "objective": s.get("objective")
                }
                for s in matched[:5]
            ]

        prompt = f"""
User profile:
{user_profile.get_profile_summary()}

User asked:
{user_text}

Matching schemes:
{schemes_info}

Answer the user's question clearly. If schemes were found, describe them. If not found locally, suggest using the official government website.
"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        await update.message.reply_text(response.content)

    except Exception as e:
        print("ERROR:", e)
        print(traceback.format_exc())
        await update.message.reply_text(
            "Something went wrong. Please try again."
        )

# ===============================
# START COMMAND HANDLER
# ===============================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - clears previous chat data and shows language selection."""
    chat_id = str(update.effective_chat.id)
    
    print(f"\n{'='*60}")
    print(f"[START COMMAND] User {chat_id} initiated fresh chat")
    print(f"{'='*60}")
    
    # Clear all previous chat data
    clear_chat_data(chat_id)
    
    # Send welcome message
    welcome_message = """
👋 Welcome to the Indian Government Schemes Assistant!

I help you find government schemes that you're eligible for.

Please select your preferred language:
"""
    
    # Create inline keyboard with language options
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
            InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hindi"),
        ],
        [
            InlineKeyboardButton("🇮🇳 मराठी", callback_data="lang_marathi"),
            InlineKeyboardButton("🇮🇳 தமிழ்", callback_data="lang_tamil"),
        ],
        [
            InlineKeyboardButton("🇮🇳 తెలుగు", callback_data="lang_telugu"),
            InlineKeyboardButton("🇮🇳 ಕನ್ನಡ", callback_data="lang_kannada"),
        ],
        [
            InlineKeyboardButton("🇮🇳 മലയാളം", callback_data="lang_malayalam"),
            InlineKeyboardButton("🇮🇳 ગુજરાતી", callback_data="lang_gujarati"),
        ],
        [
            InlineKeyboardButton("🇮🇳 ਪੰਜਾਬੀ", callback_data="lang_punjabi"),
            InlineKeyboardButton("🇮🇳 বাংলা", callback_data="lang_bengali"),
        ],
        [
            InlineKeyboardButton("🇮🇳 ओड़िया", callback_data="lang_odia"),
            InlineKeyboardButton("🇮🇳 অসমীয়া", callback_data="lang_assamese"),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# ===============================
# LANGUAGE SELECTION CALLBACK
# ===============================

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection from inline buttons."""
    query = update.callback_query
    chat_id = str(query.from_user.id)
    
    # Map callback data to language names
    language_map = {
        "lang_english": "English",
        "lang_hindi": "हिन्दी",
        "lang_marathi": "मराठी",
        "lang_tamil": "தமிழ்",
        "lang_telugu": "తెలుగు",
        "lang_kannada": "ಕನ್ನಡ",
        "lang_malayalam": "മലയാളം",
        "lang_gujarati": "ગુજરાતી",
        "lang_punjabi": "ਪੰਜਾਬੀ",
        "lang_bengali": "বাংলা",
        "lang_odia": "ओड़िया",
        "lang_assamese": "অসমীয়া",
    }
    
    selected_language = language_map.get(query.data, "English")
    
    # Store language preference in user profile
    user_profile = get_or_create_profile(chat_id)
    user_profile.add_info("language", selected_language)
    
    print(f"[LANGUAGE] User {chat_id} selected: {selected_language}")
    
    # Acknowledge the button press
    await query.answer()
    
    # Send confirmation and next steps
    lang_name = selected_language if selected_language == "English" else f"{selected_language} (Regional)"
    
    confirmation_message = f"""✅ Language set to: {lang_name}

Now, please tell me about yourself to find suitable schemes:
• Your age
• Your state/location  
• Your occupation/status (student, farmer, etc.)
• Your gender
• Any other relevant information

Example: "I'm a 22-year-old student from Maharashtra"

Then ask for eligible schemes or type "pdf" to download your eligible schemes list!

Type /help for more commands.
"""
    
    await query.edit_message_text(text=confirmation_message)

# ===============================
# BOT STARTUP
# ===============================

def main():
    print("[*] Starting Telegram bot...")

    schemes = get_all_schemes()
    print(f"[OK] Loaded {len(schemes)} schemes")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add /start command handler
    app.add_handler(CommandHandler("start", start_command))
    
    # Add language selection callback handler
    app.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
    
    # Add message handler for regular messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
