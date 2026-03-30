from dotenv import load_dotenv
import os
import sys

def load_config():
    """Load and validate environment variables."""
    if not os.path.exists(".env"):
        print("\n[ERROR] .env file not found!")
        print("Please create one by copying .env.example:")
        print("cp .env.example .env")
        sys.exit(1)

    load_dotenv()
    
    # Required keys to check
    required_keys = ["CONNECTION_STRING", "TARGET_LAT", "TARGET_LON", "TARGET_ALT"]
    missing = [key for key in required_keys if os.getenv(key) is None]
    
    if missing:
        print(f"\n[ERROR] Missing keys in .env: {', '.join(missing)}")
        sys.exit(1)