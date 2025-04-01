import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import os

class GeminiManager:
    def __init__(self):
        vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("LOCATION"))
        self.model_name = "gemini-1.5-pro-preview-0409"
        self.model = GenerativeModel(self.model_name)

    def change_model(self, model_name):
        """Changes the Gemini model being used.
        
        Args:
            model_name (str): The name of the model to use
            
        Returns:
            bool: True if the model was changed successfully, False otherwise
        """
        try:
            self.model_name = model_name
            self.model = GenerativeModel(model_name)
            return True
        except Exception as e:
            print(f"Error changing model: {str(e)}")
            return False

    def send_prompt(self, prompt):
        """Sends a text prompt to Gemini and returns the response.
        
        Args:
            prompt (str): The text prompt to send
            
        Returns:
            str: The response from Gemini
        """
        chat = self.model.start_chat()
        response = chat.send_message(prompt)
        return response.text
        
    def send_prompt_with_image(self, prompt, image_data):
        """Sends a text prompt with an image to Gemini and returns the response.
        
        Args:
            prompt (str): The text prompt to send
            image_data (bytes): The image data as a JPEG-encoded byte string
            
        Returns:
            str: The response from Gemini
        """
        try:
            # Create a multimodal prompt with the image and text
            image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
            
            # Start a chat with the model
            chat = self.model.start_chat()
            
            # Send the multimodal message
            response = chat.send_message([prompt, image_part])
            
            return response.text
        except Exception as e:
            print(f"Error sending prompt with image: {str(e)}")
            raise e
