import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import os

class GeminiManager:
    def __init__(self):
        vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("LOCATION"))
        self.model = GenerativeModel("gemini-1.5-pro-preview-0409")

    def send_prompt(self, prompt):
        """Sends a prompt to Gemini and returns the response."""
        chat = self.model.start_chat()
        response = chat.send_message(prompt)
        return response.text
