import json
import re

# --- 1. CONFIGURATION: Define what counts as "Noise" to be deleted ---
NOISE_EXACT_MATCHES = [
    "|", "Sign In", "English", "Back", "Enter scheme name to search...",
    "Check Eligibility", "Feedback", "Was this helpful?", 
    "News and Updates", "No new news and updates available",
    "Share", "Quick Links", "About Us", "Contact Us", "Screen Reader",
    "Accessibility Statement", "Disclaimer", "Terms & Conditions",
    "Dashboard", "Useful Links", "Get in touch"
]

NOISE_SUBSTRINGS = [
    "Powered by", "Digital India Corporation", "Ministry of Electronics",
    "Government of India", "Connect on Social Media", "Last Updated On",
    "copyright", "©"
]

# --- 2. CONFIGURATION: Define Headers for Content Extraction ---
HEADERS = [
    "Details", "Benefits", "Eligibility", "Exclusions", 
    "Application Process", "Documents Required", 
    "Frequently Asked Questions", "Sources And References"
]

def clean_string(text):
    """Removes extra spaces and newlines."""
    if not text:
        return None
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned if len(cleaned) > 1 else None

def is_noise_line(line):
    """Checks if a line is junk."""
    s = line.strip()
    if not s: return True
    if s in NOISE_EXACT_MATCHES: return True
    for sub in NOISE_SUBSTRINGS:
        if sub.lower() in s.lower():
            return True
    return False

def parse_scheme(entry):
    raw_text = entry.get('raw_text', '')
    url = entry.get('url', '')
    
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # --- STEP 1: EXTRACT METADATA (Name, Provider, Tags) ---
    # Strategy: Find "Check Eligibility". The lines *before* it are the metadata.
    
    provider = None
    scheme_name = None
    tags = []
    
    try:
        # Find anchor index
        anchor_idx = -1
        if "Check Eligibility" in lines:
            anchor_idx = lines.index("Check Eligibility")
        elif "Details" in lines:
            # Fallback: If 'Check Eligibility' is missing, 'Details' is usually 2-3 lines after metadata
            anchor_idx = lines.index("Details") - 1
            
        if anchor_idx >= 3:
            # Based on your file structure:
            # Line X:   Provider (e.g., "Delhi")
            # Line X+1: Scheme Name
            # Line X+2: Tags
            # Line X+3: "Check Eligibility" (Anchor)
            
            raw_tags = lines[anchor_idx - 1]
            scheme_name = lines[anchor_idx - 2]
            provider = lines[anchor_idx - 3]
            
            # Clean up Provider if it accidentally grabbed "Feedback"
            if provider == "Feedback":
                provider = lines[anchor_idx - 4] if anchor_idx >= 4 else None

            # Parse Tags (split CamelCase like "GirlChild" -> "Girl Child")
            if raw_tags and "Feedback" not in raw_tags:
                spaced_tags = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_tags)
                tags = [t.strip() for t in spaced_tags.split() if len(t) > 2]
                
    except Exception as e:
        print(f"Metadata warning for {url}: {str(e)}")

    # --- STEP 2: EXTRACT CONTENT SECTIONS ---
    # We create a dictionary to hold text for each header (Details, Benefits, etc.)
    content_map = {h: [] for h in HEADERS}
    current_header = None
    
    # Find start index (usually at "Details")
    start_processing = False
    
    for line in lines:
        # Stop completely if we hit the footer
        if "Was this helpful?" in line or "Sources And References" in line:
            # Capture Sources if needed, then stop
            if "Sources And References" in line:
                current_header = "Sources And References"
                continue
            break
            
        # Start capturing when we see the first known Header
        if line in HEADERS:
            current_header = line
            start_processing = True
            continue
            
        if start_processing and current_header:
            if not is_noise_line(line):
                content_map[current_header].append(line)

    # --- STEP 3: FORMAT OUTPUT ---
    
    # Helper to join list of lines into a single string
    def get_text(header):
        return clean_string(" ".join(content_map.get(header, [])))

    # Determine Application Mode
    process_text = get_text("Application Process") or ""
    app_mode = "Unknown"
    if "online" in process_text.lower() and "offline" in process_text.lower():
        app_mode = "Hybrid"
    elif "online" in process_text.lower():
        app_mode = "Online"
    elif "offline" in process_text.lower():
        app_mode = "Offline"

    return {
        "scheme_name": scheme_name,
        "provider": provider,
        "tags": tags,
        "application_mode": app_mode,
        "summary": get_text("Details"),
        "benefits": get_text("Benefits"),
        "eligibility_criteria": get_text("Eligibility"),
        "exclusions": get_text("Exclusions"), 
        "documents_required": get_text("Documents Required"),
        "application_process": process_text,
        "source_url": url
    }

def main():
    input_file = 'final.json'
    output_file = 'final_clean_data.json'
    
    print("Reading final.json...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cleaned_data = []
        
        print(f"Processing {len(data)} schemes...")
        
        for entry in data:
            # Parse the scheme
            result = parse_scheme(entry)
            
            # Validation: Only add if we actually found a Name or Summary
            # (This filters out empty noise entries)
            if result['scheme_name'] or result['summary']:
                cleaned_data.append(result)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
            
        print(f"Success! {len(cleaned_data)} schemes extracted.")
        print(f"Data saved to: {output_file}")
        
    except FileNotFoundError:
        print("Error: 'final.json' file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()