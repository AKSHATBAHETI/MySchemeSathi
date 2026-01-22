import json
from typing import Any
from tavily import TavilyClient
from app.config import TAVILY_API_KEY

# Global caches for DBMS-like structure
_scheme_master_cache = None
_scheme_details_cache = None

# Initialize Tavily client for web search
_tavily_client = None

def get_tavily_client():
    """Get or initialize Tavily client."""
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    return _tavily_client

def load_scheme_master(path: str = "data/scheme_master.json") -> list[dict[str, Any]]:
    """Load scheme master (lookup table) and cache."""
    global _scheme_master_cache
    if _scheme_master_cache is None:
        with open(path, "r", encoding="utf-8") as f:
            _scheme_master_cache = json.load(f)
    return _scheme_master_cache

def load_scheme_details(path: str = "data/scheme_details.json") -> list[dict[str, Any]]:
    """Load scheme details and cache."""
    global _scheme_details_cache
    if _scheme_details_cache is None:
        with open(path, "r", encoding="utf-8") as f:
            _scheme_details_cache = json.load(f)
    return _scheme_details_cache

def get_scheme_details_by_id(scheme_id: int, details_path: str = "data/scheme_details.json") -> dict[str, Any] | None:
    """Retrieve scheme details using scheme_id as foreign key."""
    details = load_scheme_details(details_path)
    for detail in details:
        if detail.get("scheme_id") == scheme_id:
            return detail
    return None

def search_scheme_master_by_name(query: str, master_path: str = "data/scheme_master.json", details_path: str = "data/scheme_details.json") -> list[int]:
    """Search scheme master by name AND scheme details (eligibility, benefits, documents) and return matching scheme IDs."""
    master = load_scheme_master(master_path)
    details = load_scheme_details(details_path)
    
    query_lower = query.lower().strip()
    tokens = [t.strip() for t in query_lower.replace("/", " ").split() if t.strip() and len(t.strip()) > 2]
    
    print(f"[SEARCH] Query: '{query}' -> Tokens (length > 2): {tokens}")
    
    exact_matches = []
    partial_matches = []
    
    # Create a details lookup by scheme_id for faster searching
    details_dict = {d.get("scheme_id"): d for d in details}
    
    for scheme in master:
        scheme_id = scheme.get("scheme_id")
        scheme_name = (scheme.get("scheme_name", "") or "").lower()
        
        # Get all searchable text from scheme details
        detail = details_dict.get(scheme_id, {})
        eligibility_text = " ".join(detail.get("eligibility", [])).lower()
        benefits_text = " ".join(detail.get("benefits", [])).lower()
        documents_text = " ".join(detail.get("documents_required", [])).lower()
        objective_text = (detail.get("objective", "") or "").lower()
        tags_text = " ".join(detail.get("tags", [])).lower()
        
        # Combine all searchable content
        searchable_text = f"{scheme_name} {objective_text} {eligibility_text} {benefits_text} {documents_text} {tags_text}"
        
        if not tokens:
            continue
        
        # Check how many tokens match
        matching_tokens = 0
        for term in tokens:
            if term in searchable_text:
                matching_tokens += 1
                print(f"[SEARCH MATCH] ID {scheme_id}: '{term}' found in '{searchable_text[:60]}'")
        
        # If all tokens match, it's an exact match
        if matching_tokens == len(tokens):
            exact_matches.append(scheme_id)
        elif matching_tokens > 0:
            partial_matches.append(scheme_id)
    
    # Prioritize exact matches first
    result = exact_matches + partial_matches
    print(f"[SEARCH RESULT] Found {len(exact_matches)} exact + {len(partial_matches)} partial = {len(result)} total")
    return result


def search_web_for_schemes(query: str) -> list[dict[str, Any]]:
    """
    Search the web using Tavily AI when data is not available locally.
    
    Args:
        query: Search query for government schemes
    
    Returns:
        List of scheme information from web search
    """
    try:
        client = get_tavily_client()
        
        # Enhance query to focus on Indian government schemes
        enhanced_query = f"Indian government schemes {query}"
        
        # Perform web search
        response = client.search(query=enhanced_query, max_results=5)
        
        web_schemes = []
        if response.get("results"):
            for i, result in enumerate(response["results"][:5], 1):
                scheme_data = {
                    "source_url": result.get("url", ""),
                    "scheme_name": result.get("title", f"Scheme {i}"),
                    "objective": result.get("content", ""),
                    "source": "web_search"
                }
                web_schemes.append(scheme_data)
        
        return web_schemes
    
    except Exception as e:
        print(f"Tavily web search error: {e}")
        return []


def search_schemes(query: str, master_path: str = "data/scheme_master.json", details_path: str = "data/scheme_details.json") -> str:
    """
    Search schemes by name and details using DBMS foreign key logic:
    1. Search in scheme_master by name AND scheme_details (eligibility, benefits, documents)
    2. Get matching scheme IDs
    3. Retrieve full details from scheme_details using scheme_id
    
    Args:
        query: User's question/search for schemes
        master_path: Path to scheme_master.json
        details_path: Path to scheme_details.json
    
    Returns:
        Formatted string with relevant schemes
    """
    # Step 1: Search master table by name AND details
    matching_ids = search_scheme_master_by_name(query, master_path, details_path)
    
    relevant_schemes = []
    
    # Load master once for efficiency
    master = load_scheme_master(master_path)
    master_dict = {m.get("scheme_id"): m.get("scheme_name") for m in master}
    
    # Step 2: If matches found, retrieve details using foreign key
    if matching_ids:
        for scheme_id in matching_ids[:5]:  # Limit to 5 results
            details = get_scheme_details_by_id(scheme_id, details_path)
            if details:
                # Add scheme_name from master dict lookup
                details["scheme_name"] = master_dict.get(scheme_id, "Unknown Scheme")
                relevant_schemes.append(details)
    
    # Step 3: If no schemes found locally, try web search
    if not relevant_schemes:
        print(f"[SEARCH] No local schemes found for '{query}'. Searching the web...")
        relevant_schemes = search_web_for_schemes(query)
    
    # Step 4: If still no schemes found, return first 5 from local database
    if not relevant_schemes:
        print(f"[SEARCH] Web search also returned nothing. Using fallback.")
        all_details = load_scheme_details(details_path)
        master = load_scheme_master(master_path)
        master_dict = {m.get("scheme_id"): m.get("scheme_name") for m in master}
        for detail in all_details[:5]:
            detail["scheme_name"] = master_dict.get(detail.get("scheme_id"))
        relevant_schemes = all_details[:5]
    
    print(f"[SEARCH] Returning {len(relevant_schemes)} formatted schemes")
    
    # Format schemes for LLM
    formatted = ""
    for i, scheme in enumerate(relevant_schemes, 1):
        source_url = scheme.get('source_url', 'Unknown')
        scheme_name = scheme.get('scheme_name', source_url.split('/')[-1] if source_url else 'Unknown')
        objective = scheme.get('objective', '')[:800]
        source = scheme.get('source', 'local')
        
        formatted += f"\n\n**Scheme {i}: {scheme_name}** [{source}]\n{objective}"
    
    return formatted


def get_all_schemes(master_path: str = "data/scheme_master.json", details_path: str = "data/scheme_details.json") -> list[dict[str, Any]]:
    """Get all schemes by joining master and details tables."""
    master = load_scheme_master(master_path)
    result = []
    
    for master_entry in master:
        scheme_id = master_entry.get("scheme_id")
        details = get_scheme_details_by_id(scheme_id, details_path)
        
        if details:
            # Combine master + details (like SQL JOIN)
            combined = {
                "scheme_id": scheme_id,
                "scheme_name": master_entry.get("scheme_name"),
                **details
            }
            result.append(combined)
    
    return result


def search_schemes_as_list(query: str, master_path: str = "data/scheme_master.json", details_path: str = "data/scheme_details.json") -> list[dict]:
    """
    Search schemes and return as list using DBMS logic, searching in both names and details.
    """
    # Step 1: Search master table and details by name, eligibility, benefits, documents
    matching_ids = search_scheme_master_by_name(query, master_path, details_path)
    
    matched = []
    
    # Step 2: Retrieve details using foreign keys
    if matching_ids:
        for scheme_id in matching_ids[:10]:
            details = get_scheme_details_by_id(scheme_id, details_path)
            if details:
                # Add scheme_name
                master = load_scheme_master(master_path)
                for m in master:
                    if m.get("scheme_id") == scheme_id:
                        details["scheme_name"] = m.get("scheme_name")
                        break
                matched.append(details)
    
    # Step 3: If no local schemes found, try web search
    if not matched:
        print(f"No local schemes found for '{query}'. Searching the web...")
        matched = search_web_for_schemes(query)
        if not matched:
            # Fallback: return first 5 from local database
            all_details = load_scheme_details(details_path)
            master = load_scheme_master(master_path)
            master_dict = {m.get("scheme_id"): m.get("scheme_name") for m in master}
            for detail in all_details[:5]:
                detail["scheme_name"] = master_dict.get(detail.get("scheme_id"))
            matched = all_details[:5]
    
    return matched

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, MODEL_NAME

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0
)

def get_eligible_schemes_using_ai(user_context: str, master_path: str = "data/scheme_master.json", details_path: str = "data/scheme_details.json") -> list[dict]:
    """
    TOKEN-SAFE AI eligibility matcher using DBMS concepts.
    - Load all eligibility tags from scheme_details
    - Match user context with eligibility criteria
    - Use scheme_id to join back with scheme_master for names
    """

    # Step 1: Load details to check eligibility
    scheme_details = load_scheme_details(details_path)
    if not scheme_details:
        return []

    # Step 2: Simple keyword extraction from user context
    context_lower = user_context.lower()
    context_keywords = set(context_lower.split())

    # Step 3: LOCAL PRE-FILTER (check eligibility tags and objectives)
    shortlisted_ids = []
    for detail in scheme_details:
        eligibility_text = " ".join(detail.get("eligibility", [])).lower()
        objective_text = (detail.get("objective", "") or "").lower()
        tags_text = " ".join(detail.get("tags", [])).lower()
        
        searchable_text = f"{eligibility_text} {objective_text} {tags_text}"

        if any(word in searchable_text for word in context_keywords):
            shortlisted_ids.append(detail.get("scheme_id"))

        if len(shortlisted_ids) >= 8:  # HARD LIMIT - check all but return max 8
            break

    if not shortlisted_ids:
        return []

    # Step 4: JOIN operation - get scheme names from master
    scheme_master = load_scheme_master(master_path)
    master_dict = {s.get("scheme_id"): s.get("scheme_name") for s in scheme_master}
    
    scheme_lines = []
    shortlisted_details = []
    for scheme_id in shortlisted_ids:
        scheme_name = master_dict.get(scheme_id, "Unknown")
        scheme_lines.append(f"{scheme_id}. {scheme_name}")
        # Also get the details for later use
        details = get_scheme_details_by_id(scheme_id, details_path)
        if details:
            shortlisted_details.append(details)

    # Step 5: BUILD A SMALL PROMPT
    prompt = f"""
You are an Indian government scheme eligibility expert.

User information:
{user_context}

Below is a SHORT list of schemes with IDs.
Select ONLY those the user is clearly eligible for based on eligibility criteria.

Schemes:
{chr(10).join(scheme_lines)}

Return ONLY valid JSON in this format:
[
  {{
    "scheme_id": 1,
    "eligibility_reason": "short reason"
  }}
]

Rules:
- If eligibility is unclear, EXCLUDE the scheme
- Max 5 schemes
- Must include scheme_id
"""

    # Step 6: AI CALL (SAFE SIZE)
    response = llm.invoke([HumanMessage(content=prompt)])

    # Step 7: PARSE AND JOIN RESULTS
    try:
        import json
        
        # Try to extract JSON from response
        response_text = response.content.strip()
        print(f"[AI RESPONSE] {response_text[:100]}...")
        
        # Find JSON array in response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            print("[ERROR] No JSON array found in response")
            return []
        
        json_str = response_text[json_start:json_end]
        result = json.loads(json_str)
        
        if not isinstance(result, list):
            print(f"[ERROR] Response is not a list: {type(result)}")
            return []

        print(f"[AI] Parsed {len(result)} schemes from AI response")
        
        # Attach scheme details and names using scheme_id
        final = []
        for r in result:
            scheme_id = r.get("scheme_id")
            scheme_name = master_dict.get(scheme_id)
            details = get_scheme_details_by_id(scheme_id, details_path)
            
            if details and scheme_name:
                final.append({
                    "scheme_id": scheme_id,
                    "scheme_name": scheme_name,
                    "source_url": details.get("source_url", ""),
                    "objective": details.get("objective", "")[:800],
                    "eligibility_reason": r.get("eligibility_reason", "")
                })
        
        print(f"[AI] Returning {len(final)} eligible schemes")
        return final

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}")
        print(f"[ERROR] Response was: {response.content[:200]}")
        return []
    except Exception as e:
        print(f"[ERROR] Eligibility matching error: {e}")
        import traceback
        traceback.print_exc()
        return []
