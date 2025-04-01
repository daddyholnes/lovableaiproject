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

    # Conversation ID
    conversation_id = "conversation_1"

    while True:
        # Load previous interactions
        interactions = storage_manager.list_interactions(conversation_id)
        chat_history = ""
        for interaction_id in range(1, len(interactions) + 1):
            interaction = storage_manager.get_interaction(conversation_id, interaction_id)
            if interaction:
                chat_history += f"{interaction['role']}: {interaction['content']}\n"

        # Get user input
        user_prompt = input("You: ")
        if user_prompt.lower() == "exit":
            break

        # Send prompt to Gemini
        full_prompt = f"""
        {chat_history}
        {user_prompt}
        """
        gemini_response = gemini_manager.send_prompt(full_prompt)

        # Save interaction to storage
        storage_manager.save_interaction(conversation_id, "user", user_prompt)
        storage_manager.save_interaction(conversation_id, "gemini", gemini_response)

        # Print Gemini's response
        print(f"Gemini: {gemini_response}")

        # TODO: Remove or comment out any calls to gemini_ui.py or functions that depend on cv2 here

if __name__ == "__main__":
    main()
