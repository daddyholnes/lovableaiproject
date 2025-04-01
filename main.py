from utils.gemini_manager import GeminiManager
from utils.storage_manager import StorageManager
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """Main function to run the Persistent Gemini Workspace."""

    # Initialize the Storage Manager
    storage_manager = StorageManager(bucket_name=os.getenv("BUCKET_NAME"))

    # Initialize the Gemini Manager
    gemini_manager = GeminiManager()

    # Example: Start a new conversation
    conversation_id = "conversation_1"  # You can generate a unique ID here
    initial_prompt = "You are my project leader. Let's start a new project."
    gemini_response = gemini_manager.send_prompt(initial_prompt)

    # Save the initial interaction to storage
    storage_manager.save_interaction(conversation_id, "user", initial_prompt)
    storage_manager.save_interaction(conversation_id, "gemini", gemini_response)

    print(f"Gemini: {gemini_response}")

if __name__ == "__main__":
    main()
