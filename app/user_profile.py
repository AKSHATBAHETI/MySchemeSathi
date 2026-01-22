"""
User profile management - stores user information for scheme matching
"""

class UserProfile:
    """Stores user information provided during conversation."""
    
    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        self.profile_data = {
            "age": None,
            "income": None,
            "state": None,
            "occupation": None,
            "education": None,
            "gender": None,
            "caste": None,
            "disability": None,
            "employment_status": None,
            "business_type": None,
            "family_income": None,
            "has_land": None,
            "language": "English",  # Default language
            "raw_text": []  # Store raw user messages for AI context
        }
    
    def add_info(self, key: str, value):
        """Add or update user information."""
        if key in self.profile_data:
            self.profile_data[key] = value
    
    def add_raw_text(self, text: str):
        """Add raw user message for context."""
        self.profile_data["raw_text"].append(text)
    
    def get_profile(self) -> dict:
        """Get full profile."""
        return self.profile_data
    
    def get_profile_summary(self) -> str:
        """Get a text summary of collected information."""
        summary = []
        for key, value in self.profile_data.items():
            if value and key != "raw_text":
                summary.append(f"{key}: {value}")
        
        if self.profile_data["raw_text"]:
            summary.append(f"\nUser messages: {' | '.join(self.profile_data['raw_text'][:5])}")
        
        return "\n".join(summary)
    
    def is_empty(self) -> bool:
        """Check if profile has any meaningful data."""
        return all(v is None for k, v in self.profile_data.items() if k != "raw_text") and not self.profile_data["raw_text"]


# Global storage for user profiles
user_profiles: dict[str, UserProfile] = {}


def get_or_create_profile(chat_id: str) -> UserProfile:
    """Get existing profile or create new one."""
    if chat_id not in user_profiles:
        user_profiles[chat_id] = UserProfile(chat_id)
    return user_profiles[chat_id]


def get_profile(chat_id: str) -> UserProfile | None:
    """Get user profile by chat ID."""
    return user_profiles.get(chat_id)


def clear_profile(chat_id: str):
    """Clear user profile."""
    if chat_id in user_profiles:
        del user_profiles[chat_id]
