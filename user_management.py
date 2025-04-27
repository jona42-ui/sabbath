from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import hashlib
import jwt
from pathlib import Path

class UserManager:
    def __init__(self):
        self.users_dir = Path("data/users")
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Should be in .env

    def create_user(self, username: str, password: str, email: str) -> Dict:
        """Create a new user with SDA-focused profile"""
        if self._user_exists(username):
            raise ValueError("Username already exists")

        salt = os.urandom(32)
        password_hash = self._hash_password(password, salt)
        
        user = {
            "username": username,
            "email": email,
            "password_hash": password_hash.hex(),
            "salt": salt.hex(),
            "created_at": datetime.now().isoformat(),
            "profile": {
                "sabbath_preferences": {
                    "preparation_start_hour": 14,  # Default to Friday 2 PM
                    "notification_hours_before": 24,
                    "auto_mode": True
                },
                "spiritual_goals": {
                    "bible_study": {
                        "daily_chapters": 1,
                        "study_time_minutes": 30,
                        "memorization_verses_per_week": 1
                    },
                    "prayer": {
                        "morning_prayer": True,
                        "evening_prayer": True,
                        "prayer_time_minutes": 15
                    },
                    "health": {
                        "rest_hours": 8,
                        "water_glasses": 8,
                        "exercise_minutes": 30
                    }
                },
                "doctrinal_interests": [
                    "sabbath",
                    "health_message",
                    "prophecy",
                    "sanctuary"
                ],
                "ministry_involvement": []
            }
        }

        self._save_user(username, user)
        return {k: v for k, v in user.items() if k != "password_hash" and k != "salt"}

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token if successful"""
        user = self._load_user(username)
        if not user:
            return None

        salt = bytes.fromhex(user["salt"])
        password_hash = bytes.fromhex(user["password_hash"])
        
        if self._hash_password(password, salt) == password_hash:
            token = jwt.encode(
                {
                    "username": username,
                    "exp": datetime.utcnow() + timedelta(days=1)
                },
                self.secret_key,
                algorithm="HS256"
            )
            return token
        return None

    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user profile without sensitive information"""
        user = self._load_user(username)
        if user:
            return {
                "username": user["username"],
                "email": user["email"],
                "profile": user["profile"],
                "created_at": user["created_at"]
            }
        return None

    def update_profile(self, username: str, profile_updates: Dict) -> bool:
        """Update user profile settings"""
        user = self._load_user(username)
        if not user:
            return False

        user["profile"].update(profile_updates)
        self._save_user(username, user)
        return True

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return username if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload["username"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def _user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return (self.users_dir / f"{username}.json").exists()

    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """Hash password with salt using SHA-256"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # Number of iterations
        )

    def _save_user(self, username: str, user_data: Dict) -> None:
        """Save user data to file"""
        with open(self.users_dir / f"{username}.json", 'w') as f:
            json.dump(user_data, f, indent=2)

    def _load_user(self, username: str) -> Optional[Dict]:
        """Load user data from file"""
        try:
            with open(self.users_dir / f"{username}.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
