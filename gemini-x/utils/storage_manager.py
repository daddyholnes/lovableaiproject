from google.cloud import storage
import json
import os

class StorageManager:
    def __init__(self, bucket_name):
        self.client = storage.Client()
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)

    def save_interaction(self, conversation_id, role, content):
        """Saves an interaction to Google Cloud Storage."""
        blob_name = f"{conversation_id}/{len(self.list_interactions(conversation_id)) + 1}.json"
        blob = self.bucket.blob(blob_name)
        data = {"role": role, "content": content}
        blob.upload_from_string(json.dumps(data), content_type="application/json")

    def list_interactions(self, conversation_id):
        """Lists all interactions for a given conversation."""
        blobs = self.client.list_blobs(self.bucket_name, prefix=f"{conversation_id}/")
        return [blob.name for blob in blobs]

    def get_interaction(self, conversation_id, interaction_id):
        """Gets a specific interaction from Google Cloud Storage."""
        blob_name = f"{conversation_id}/{interaction_id}.json"
        blob = self.bucket.blob(blob_name)
        if blob.exists():
            return json.loads(blob.download_as_string())
        else:
            return None
            
    def clear_storage(self, conversation_id):
        """Clears all interactions for a given conversation from Google Cloud Storage.
        
        Args:
            conversation_id (str): The ID of the conversation to clear
            
        Returns:
            int: The number of blobs deleted
        """
        try:
            # List all blobs in the conversation
            blobs = list(self.client.list_blobs(
                self.bucket_name, 
                prefix=f"{conversation_id}/"
            ))
            
            # Delete each blob
            for blob in blobs:
                blob.delete()
                
            return len(blobs)
        except Exception as e:
            print(f"Error clearing storage: {str(e)}")
            return -1
