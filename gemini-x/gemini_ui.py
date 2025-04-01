import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import cv2
import threading
import time
import numpy as np
import io
from datetime import datetime
from PIL import Image, ImageTk
from dotenv import load_dotenv
from utils.gemini_manager import GeminiManager
from utils.storage_manager import StorageManager
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from vertexai.preview.generative_models import GenerativeModel, Part
from vertexai.exceptions import VertexAIError
import mss
import speech_recognition as sr
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='gemini_x.log'
)
logger = logging.getLogger('GeminiX')

# Load environment variables
load_dotenv()

class GeminiXError(Exception):
    """Base exception class for GeminiX application errors"""
    pass

class WebcamError(GeminiXError):
    """Exception raised for errors in webcam operations"""
    pass

class ScreenshareError(GeminiXError):
    """Exception raised for errors in screenshare operations"""
    pass

class MicrophoneError(GeminiXError):
    """Exception raised for errors in microphone operations"""
    pass

class GeminiXApp:
    """Main application class for the Gemini X interface"""
    
    def __init__(self, root):
        """Initialize the application
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        
        # Configure the window
        self.root.title("Gemini X")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Set background color
        self.bg_color = "#f8f9fa"  # Light gray background
        self.text_bg_color = "#e9ecef"  # Darker gray for text areas
        self.accent_color = "#4285f4"  # Google blue
        self.root.configure(bg=self.bg_color)
        
        # Add a variable to store the selected model
        self.selected_model = tk.StringVar(value="gemini-1.5-pro-preview-0409")
        
        try:
            # Initialize the Storage Manager
            bucket_name = os.getenv("BUCKET_NAME")
            if not bucket_name:
                raise ValueError("BUCKET_NAME environment variable not set")
            
            self.storage_manager = StorageManager(bucket_name=bucket_name)
            
            # Initialize the Gemini Manager
            project_id = os.getenv("PROJECT_ID")
            location = os.getenv("LOCATION")
            if not project_id or not location:
                raise ValueError("PROJECT_ID or LOCATION environment variables not set")
            
            self.gemini_manager = GeminiManager()
            
            # Conversation ID
            self.conversation_id = "conversation_1"
            
            # Initialize UI component states
            self._initialize_component_states()
            
            # Create the UI
            self._create_menu_bar()
            self._create_main_layout()
            self._create_status_bar()
            
            # Show initial status message
            self.update_status("Ready - Gemini X initialized")
            
            # Set up cleanup on window close
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except ValueError as e:
            logger.error(f"Initialization error: {str(e)}")
            messagebox.showerror("Configuration Error", f"Error initializing application: {str(e)}")
            self.root.quit()
        except GoogleCloudError as e:
            logger.error(f"Google Cloud error: {str(e)}")
            messagebox.showerror("Storage Error", f"Error connecting to Google Cloud: {str(e)}")
            self.root.quit()
        except Exception as e:
            logger.error(f"Unexpected initialization error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred during initialization: {str(e)}")
            self.root.quit()
            
    def _initialize_component_states(self):
        """Initialize the state variables for UI components"""
        # Webcam variables
        self.webcam = None
        self.webcam_window = None
        self.webcam_thread = None
        self.webcam_running = False
        
        # Screenshare variables
        self.sct = None
        self.screenshare_window = None
        self.screenshare_thread = None
        self.screenshare_running = False
        self.screen_image = None
        
        # Microphone variables
        self.recognizer = None
        self.microphone = None
        self.microphone_window = None
        self.listening_thread = None
        self.listening = False
        self.audio_text = ""
        
        # Create the UI
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        
        # Show initial status message
        self.update_status("Ready - Gemini X initialized")
        
        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_menu_bar(self):
        """Create the application menu bar"""
        menu_bar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Conversation", command=self.new_conversation)
        file_menu.add_command(label="Clear Conversation", command=self.clear_conversation)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Model Menu
        model_menu = tk.Menu(menu_bar, tearoff=0)
        model_menu.add_command(label="Select Model", command=self.select_model)
        menu_bar.add_cascade(label="Model", menu=model_menu)
        
        # Multimodal Menu
        multimodal_menu = tk.Menu(menu_bar, tearoff=0)
        multimodal_menu.add_command(label="Webcam", command=self.webcam_functionality)
        multimodal_menu.add_command(label="Screenshare", command=self.screenshare_functionality)
        multimodal_menu.add_command(label="Microphone", command=self.microphone_functionality)
        menu_bar.add_cascade(label="Multimodal", menu=multimodal_menu)
        
        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)

    def _create_main_layout(self):
        """Create the main window layout using grid"""
        # Create a frame for the toolbar area (model selection, etc.)
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        # Create and add model selection dropdown
        model_label = ttk.Label(toolbar_frame, text="Model:")
        model_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create the model dropdown with the available options
        model_options = [
            "gemini-1.5-pro-preview-0409",
            "gemini-1.5-flash-preview-0514",
            "gemini-1.0-pro-001",
            "gemini-1.0-pro-vision-001"
        ]
        
        model_dropdown = ttk.Combobox(
            toolbar_frame,
            textvariable=self.selected_model,
            values=model_options,
            state="readonly",
            width=25
        )
        # Add callback for model selection
        model_dropdown.bind("<<ComboboxSelected>>", self.on_model_change)
        model_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create multimodal buttons (right side of toolbar)
        webcam_button = ttk.Button(toolbar_frame, text="Webcam", command=self.webcam_functionality)
        webcam_button.pack(side=tk.RIGHT, padx=5)
        
        screenshare_button = ttk.Button(toolbar_frame, text="Screenshare", command=self.screenshare_functionality)
        screenshare_button.pack(side=tk.RIGHT, padx=5)
        
        microphone_button = ttk.Button(toolbar_frame, text="Microphone", command=self.microphone_functionality)
        microphone_button.pack(side=tk.RIGHT, padx=5)
        
        # Main content area using grid layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid layout with weights for resizing
        main_frame.columnconfigure(0, weight=1)  # Output area column
        main_frame.rowconfigure(0, weight=0)  # Output label row - fixed height
        main_frame.rowconfigure(1, weight=6)  # Output area row - expands with window
        main_frame.rowconfigure(2, weight=0)  # Input label row - fixed height
        main_frame.rowconfigure(3, weight=1)  # Input area row - expands with window, but less than output
        
        # Output area label
        output_label = ttk.Label(main_frame, text="Conversation:")
        output_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Output area (conversation history) - read-only
        self.output_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=("Segoe UI", 10),
            bg=self.text_bg_color,
            state="disabled"  # Make it read-only
        )
        self.output_area.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        # Input area label
        input_label = ttk.Label(main_frame, text="Prompt:")
        input_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        # Input area (user prompt)
        self.input_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=50,
            height=5,
            font=("Segoe UI", 10),
            bg=self.text_bg_color
        )
        self.input_area.grid(row=3, column=0, sticky="nsew")
        
        # Send button
        send_button = ttk.Button(main_frame, text="Send", command=self.send_to_gemini)
        send_button.grid(row=4, column=0, sticky="e", pady=(5, 0))
        
        # Clear button
        clear_button = ttk.Button(main_frame, text="Clear", command=self.clear_conversation)
        clear_button.grid(row=4, column=0, sticky="w", pady=(5, 0))

    def _create_status_bar(self):
        """Create status bar at the bottom of the window"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var,
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            padding=(5, 2)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """Update the status bar with a message.
        
        Args:
            message (str): The message to display in the status bar
        """
        self.status_var.set(message)
        self.root.update_idletasks()  # Force update of the UI
        
    def add_to_conversation(self, role, text):
        """Add a message to the conversation history.
        
        Args:
            role (str): The role of the sender (e.g., 'You', 'Gemini')
            text (str): The message text
        """
        self.output_area.config(state="normal")  # Enable editing
        
        # Add role header with formatting
        self.output_area.insert(tk.END, f"\n{role}: ", "role")
        # Add message content
        self.output_area.insert(tk.END, f"{text}\n", "message")
        
        # Scroll to the end of the conversation
        self.output_area.see(tk.END)
        self.output_area.config(state="disabled")  # Disable editing again
        
    def send_to_gemini(self, user_input=None, image_data=None, audio_text=None):
        """Process user input and send to Gemini API
        
        Args:
            user_input (str, optional): The user's text input. If None, gets from the input area.
            image_data (bytes, optional): Image data to send to Gemini.
            audio_text (str, optional): Transcribed audio text to send to Gemini.
        """
        # Get the user's input if not provided
        if user_input is None:
            user_input = self.input_area.get("1.0", tk.END).strip()
            
            if not user_input and not image_data and not audio_text:
                # Don't process empty messages
                self.update_status("Please enter a prompt before sending.")
                return
                
            # Clear the input area
            self.input_area.delete("1.0", tk.END)
            
            # Add user message to conversation history
            self.add_to_conversation("You", user_input)
        
        # If audio_text is provided, use it instead of user_input
        if audio_text:
            user_input = audio_text
        
        # Update status
        self.update_status("Sending prompt to Gemini...")
        
        try:
            # Send the prompt to Gemini
            if image_data:
                # Create a multimodal prompt with image and text
                gemini_response = self.gemini_manager.send_prompt_with_image(user_input, image_data)
            else:
                # Send text-only prompt
                gemini_response = self.gemini_manager.send_prompt(user_input)
            
            # Add Gemini's response to conversation history
            self.add_to_conversation("Gemini", gemini_response)
            
            # Save the interaction
            self.storage_manager.save_interaction(self.conversation_id, "user", user_input)
            self.storage_manager.save_interaction(self.conversation_id, "gemini", gemini_response)
            
            # Update status
            self.update_status("Response received and displayed.")
        except VertexAIError as e:
            logger.error(f"Vertex AI error: {str(e)}")
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        except GoogleCloudError as e:
            logger.error(f"Google Cloud error: {str(e)}")
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def clear_conversation(self):
        """Clear the conversation history in the output area and cloud storage"""
        # Enable editing of the output area
        self.output_area.config(state="normal")
        
        # Delete all content
        self.output_area.delete("1.0", tk.END)
        
        # Disable editing again
        self.output_area.config(state="disabled")
        
        # Clear the cloud storage
        self.clear_cloud_storage()
        
        # Update the status bar
        self.update_status("Conversation cleared")

    def clear_cloud_storage(self):
        """Clear interactions from Google Cloud Storage for the current conversation"""
        try:
            # Use the storage_manager to clear the cloud storage
            deleted_count = self.storage_manager.clear_storage(self.conversation_id)
            
            if deleted_count >= 0:
                self.update_status(f"Cleared {deleted_count} messages from cloud storage")
            else:
                self.update_status("Failed to clear cloud storage")
                messagebox.showerror("Error", "Failed to clear cloud storage")
        except GoogleCloudError as e:
            logger.error(f"Google Cloud error: {str(e)}")
            self.update_status(f"Error clearing cloud storage: {str(e)}")
            messagebox.showerror("Error", f"Failed to clear cloud storage: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error clearing cloud storage: {str(e)}")
            messagebox.showerror("Error", f"Failed to clear cloud storage: {str(e)}")

    # Menu bar functionality methods
    
    def new_conversation(self):
        """Handle the New Conversation menu item click"""
        # Clear the conversation history (reuse clear_conversation method)
        self.clear_conversation()
        
        # Clear the cloud storage
        self.clear_cloud_storage()
        
        # Update the status bar with a different message
        self.update_status("New conversation started")
    
    def exit_application(self):
        """Handle the Exit menu item click"""
        self.root.quit()
    
    def select_model(self):
        """Handle the Select Model menu item click"""
        messagebox.showinfo("Select Model", "Select a model from the dropdown menu")
        self.update_status("Select a model from the dropdown menu")
    
    def on_model_change(self, event):
        """Handle the model selection change event"""
        new_model = self.selected_model.get()
        
        try:
            # Update the Gemini manager with the new model
            success = self.gemini_manager.change_model(new_model)
            
            if success:
                # Update status bar
                self.update_status(f"Model changed to {new_model}")
            else:
                self.update_status(f"Failed to change model to {new_model}")
                messagebox.showerror("Error", f"Failed to change model to {new_model}")
        except VertexAIError as e:
            logger.error(f"Vertex AI error: {str(e)}")
            self.update_status(f"Error changing model: {str(e)}")
            messagebox.showerror("Error", f"Failed to change model: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error changing model: {str(e)}")
            messagebox.showerror("Error", f"Failed to change model: {str(e)}")
    
    def webcam_functionality(self):
        """Handle the Webcam menu item click or button click"""
        if self.webcam_running:
            self.update_status("Webcam is already running")
            return
            
        self.update_status("Opening webcam...")
        
        try:
            # Open the default webcam (index 0)
            self.webcam = cv2.VideoCapture(0)
            
            if not self.webcam.isOpened():
                raise WebcamError("Could not open webcam")
                
            # Create a new window for the webcam feed
            self.webcam_window = tk.Toplevel(self.root)
            self.webcam_window.title("Webcam Feed")
            self.webcam_window.geometry("640x520")  # Enough space for video and buttons
            self.webcam_window.protocol("WM_DELETE_WINDOW", self.close_webcam)
            
            # Create a label to display the video feed
            self.video_label = ttk.Label(self.webcam_window)
            self.video_label.pack(pady=10)
            
            # Create buttons frame
            button_frame = ttk.Frame(self.webcam_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Create buttons
            capture_button = ttk.Button(button_frame, text="Capture Screenshot", command=self.capture_screenshot)
            capture_button.pack(side=tk.LEFT, padx=5)
            
            # Add "Send to Gemini" button
            send_to_gemini_button = ttk.Button(button_frame, text="Send to Gemini", command=self.send_webcam_to_gemini)
            send_to_gemini_button.pack(side=tk.LEFT, padx=5)
            
            close_button = ttk.Button(button_frame, text="Close Webcam", command=self.close_webcam)
            close_button.pack(side=tk.RIGHT, padx=5)
            
            # Start webcam in a separate thread
            self.webcam_running = True
            self.webcam_thread = threading.Thread(target=self.show_webcam_feed)
            self.webcam_thread.daemon = True  # Thread will close when main program exits
            self.webcam_thread.start()
            
            self.update_status("Webcam opened")
            
        except WebcamError as e:
            if self.webcam:
                self.webcam.release()
            logger.error(f"Webcam error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.update_status(f"Error opening webcam: {str(e)}")
        except Exception as e:
            if self.webcam:
                self.webcam.release()
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self.update_status(f"Error opening webcam: {str(e)}")
    
    def show_webcam_feed(self):
        """Display the webcam feed in the video label"""
        try:
            while self.webcam_running:
                # Read a frame from the webcam
                ret, frame = self.webcam.read()
                
                if ret:
                    # Convert the frame from BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PhotoImage format for tkinter
                    img = Image.fromarray(frame_rgb)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    # Update the video label
                    self.video_label.configure(image=imgtk)
                    self.video_label.image = imgtk  # Keep a reference to avoid garbage collection
                
                # Small delay to prevent high CPU usage
                time.sleep(0.03)  # About 30 frames per second
        except Exception as e:
            logger.error(f"Error in webcam thread: {str(e)}", exc_info=True)
            self.close_webcam()
    
    def capture_screenshot(self, save_to_file=True):
        """Capture a screenshot from the webcam feed
        
        Args:
            save_to_file (bool): Whether to save the screenshot to a file
            
        Returns:
            bytes: The image data as a JPEG-encoded byte string if save_to_file is False,
                  None otherwise
        """
        if not self.webcam_running:
            return None
            
        try:
            # Read a frame from the webcam
            ret, frame = self.webcam.read()
            
            if ret:
                if save_to_file:
                    # Create a filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                    filename = os.path.join(desktop_path, f"gemini_screenshot_{timestamp}.jpg")
                    
                    # Save the frame as a JPEG image
                    cv2.imwrite(filename, frame)
                    
                    self.update_status(f"Screenshot saved to {filename}")
                    messagebox.showinfo("Screenshot", f"Screenshot saved to {filename}")
                    return None
                else:
                    # Convert the image to JPEG byte string
                    _, buffer = cv2.imencode('.jpg', frame)
                    return buffer.tobytes()
            else:
                raise WebcamError("Failed to capture screenshot")
        except WebcamError as e:
            logger.error(f"Webcam error: {str(e)}")
            self.update_status(f"Error capturing screenshot: {str(e)}")
            messagebox.showerror("Error", f"Error capturing screenshot: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error capturing screenshot: {str(e)}")
            messagebox.showerror("Error", f"Error capturing screenshot: {str(e)}")
            return None
    
    def send_webcam_to_gemini(self):
        """Capture a screenshot from the webcam and send it to Gemini"""
        try:
            # Update status
            self.update_status("Capturing image from webcam...")
            
            # Get the image data
            image_data = self.capture_screenshot(save_to_file=False)
            
            if image_data:
                # Update status
                self.update_status("Sending image to Gemini...")
                
                # Add a prompt text
                prompt_text = "Tell me what you see in this webcam image."
                
                # Add the image to the conversation history
                self.output_area.config(state="normal")
                self.output_area.insert(tk.END, "\nYou: [Sent a webcam image with text: \"" + prompt_text + "\"]\n", "role")
                self.output_area.see(tk.END)
                self.output_area.config(state="disabled")
                
                # Send to Gemini
                self.send_to_gemini(prompt_text, image_data=image_data)
            else:
                self.update_status("Failed to capture webcam image")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error sending webcam image to Gemini: {str(e)}")
            messagebox.showerror("Error", f"Error sending webcam image to Gemini: {str(e)}")
    
    def close_webcam(self):
        """Close the webcam and release resources"""
        if self.webcam_running:
            self.webcam_running = False
            
            # Give the thread time to finish
            if self.webcam_thread:
                self.webcam_thread.join(1.0)
            
            # Release the webcam
            if self.webcam:
                self.webcam.release()
                self.webcam = None
            
            # Close the window
            if self.webcam_window:
                self.webcam_window.destroy()
                self.webcam_window = None
            
            self.update_status("Webcam closed")

    def screenshare_functionality(self):
        """Handle the Screenshare menu item click or button click"""
        if self.screenshare_running:
            self.update_status("Screenshare is already running")
            return
            
        self.update_status("Opening screenshare...")
        
        try:
            # Initialize screen capture
            self.sct = mss.mss()
            
            # Create a new window for the screen capture
            self.screenshare_window = tk.Toplevel(self.root)
            self.screenshare_window.title("Screen Capture")
            self.screenshare_window.geometry("800x600")  # Default size
            self.screenshare_window.protocol("WM_DELETE_WINDOW", self.close_screenshare)
            
            # Create a label to display the screen capture
            self.screen_label = ttk.Label(self.screenshare_window)
            self.screen_label.pack(pady=10, expand=True, fill=tk.BOTH)
            
            # Create buttons frame
            button_frame = ttk.Frame(self.screenshare_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Create buttons
            capture_button = ttk.Button(button_frame, text="Capture Screenshot", command=self.capture_screen)
            capture_button.pack(side=tk.LEFT, padx=5)
            
            # Add "Send to Gemini" button
            send_to_gemini_button = ttk.Button(button_frame, text="Send to Gemini", command=self.send_screenshare_to_gemini)
            send_to_gemini_button.pack(side=tk.LEFT, padx=5)
            
            save_button = ttk.Button(button_frame, text="Save Screenshot", command=self.save_screenshot)
            save_button.pack(side=tk.LEFT, padx=5)
            
            close_button = ttk.Button(button_frame, text="Close Screenshare", command=self.close_screenshare)
            close_button.pack(side=tk.RIGHT, padx=5)
            
            # Perform initial screen capture
            self.capture_screen()
            
            self.screenshare_running = True
            self.update_status("Screenshare opened")
            
        except ScreenshareError as e:
            if self.sct:
                self.sct.close()
            logger.error(f"Screenshare error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.update_status(f"Error opening screenshare: {str(e)}")
        except Exception as e:
            if self.sct:
                self.sct.close()
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self.update_status(f"Error opening screenshare: {str(e)}")
    
    def capture_screen(self):
        """Capture the screen and display it in the window
        
        Returns:
            bool: True if capture successful, False otherwise
            bytes: Image data as JPEG byte string if requested, None otherwise
        """
        try:
            # Capture entire screen
            monitor = self.sct.monitors[0]  # First monitor (entire screen)
            screenshot = self.sct.grab(monitor)
            
            # Convert to an array
            img = np.array(screenshot)
            
            # Convert from BGRA to RGB for display
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            
            # Resize to fit in window if needed
            window_width = self.screenshare_window.winfo_width()
            window_height = self.screenshare_window.winfo_height()
            
            if window_width > 100 and window_height > 100:  # Ensure window is properly sized
                aspect_ratio = img_rgb.shape[1] / img_rgb.shape[0]
                new_width = window_width - 20
                new_height = int(new_width / aspect_ratio)
                
                if new_height > window_height - 100:  # Account for buttons
                    new_height = window_height - 100
                    new_width = int(new_height * aspect_ratio)
                
                img_rgb_resized = cv2.resize(img_rgb, (new_width, new_height))
                
                # Convert to PhotoImage format for tkinter
                pil_img = Image.fromarray(img_rgb_resized)
                self.screen_image = ImageTk.PhotoImage(image=pil_img)
            else:
                # Convert to PhotoImage format for tkinter
                pil_img = Image.fromarray(img_rgb)
                self.screen_image = ImageTk.PhotoImage(image=pil_img)
            
            # Update the screen label
            self.screen_label.configure(image=self.screen_image)
            
            # Save the latest screenshot for saving
            self.latest_screenshot = img
            
            # Convert to JPEG for Gemini API (use original image, not resized)
            _, buffer = cv2.imencode('.jpg', img_rgb)
            self.latest_screenshot_jpeg = buffer.tobytes()
            
            return True
        except ScreenshareError as e:
            logger.error(f"Screenshare error: {str(e)}")
            self.update_status(f"Error capturing screen: {str(e)}")
            messagebox.showerror("Error", f"Error capturing screen: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error capturing screen: {str(e)}")
            messagebox.showerror("Error", f"Error capturing screen: {str(e)}")
            return False
    
    def send_screenshare_to_gemini(self):
        """Send the current screenshot to Gemini for analysis"""
        try:
            # Check if we have a screenshot
            if not hasattr(self, 'latest_screenshot_jpeg') or not self.latest_screenshot_jpeg:
                # Try to capture a new one
                if not self.capture_screen():
                    self.update_status("Failed to capture screenshot for Gemini")
                    return
            
            # Update status
            self.update_status("Sending screenshot to Gemini...")
            
            # Add a prompt text
            prompt_text = "Tell me what you see in this screenshot."
            
            # Add the image to the conversation history
            self.output_area.config(state="normal")
            self.output_area.insert(tk.END, "\nYou: [Sent a screenshot with text: \"" + prompt_text + "\"]\n", "role")
            self.output_area.see(tk.END)
            self.output_area.config(state="disabled")
            
            # Send to Gemini
            self.send_to_gemini(prompt_text, image_data=self.latest_screenshot_jpeg)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error sending screenshot to Gemini: {str(e)}")
            messagebox.showerror("Error", f"Error sending screenshot to Gemini: {str(e)}")
    
    def save_screenshot(self):
        """Save the captured screenshot to the desktop"""
        try:
            if hasattr(self, 'latest_screenshot'):
                # Create a filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                filename = os.path.join(desktop_path, f"gemini_screen_{timestamp}.png")
                
                # Save the screenshot
                cv2.imwrite(filename, self.latest_screenshot)
                
                self.update_status(f"Screenshot saved to {filename}")
                messagebox.showinfo("Screenshot", f"Screenshot saved to {filename}")
            else:
                raise ScreenshareError("No screenshot to save")
        except ScreenshareError as e:
            logger.error(f"Screenshare error: {str(e)}")
            self.update_status(f"Error saving screenshot: {str(e)}")
            messagebox.showerror("Error", f"Error saving screenshot: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error saving screenshot: {str(e)}")
            messagebox.showerror("Error", f"Error saving screenshot: {str(e)}")
    
    def close_screenshare(self):
        """Close the screenshare window and release resources"""
        if self.screenshare_running:
            self.screenshare_running = False
            
            # Close screen capture
            if self.sct:
                self.sct.close()
                self.sct = None
            
            # Close the window
            if self.screenshare_window:
                self.screenshare_window.destroy()
                self.screenshare_window = None
            
            self.update_status("Screenshare closed")
    
    def microphone_functionality(self):
        """Handle the Microphone menu item click or button click"""
        if self.listening:
            self.update_status("Microphone is already active")
            return
            
        self.update_status("Starting microphone...")
        
        try:
            # Initialize the recognizer and microphone
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Create a new window for the microphone
            self.microphone_window = tk.Toplevel(self.root)
            self.microphone_window.title("Microphone")
            self.microphone_window.geometry("500x300")
            self.microphone_window.protocol("WM_DELETE_WINDOW", self.stop_listening)
            
            # Add a label with instructions
            instructions_label = ttk.Label(
                self.microphone_window, 
                text="Click 'Start Listening' to begin recording audio.\nSpeak clearly into your microphone.",
                font=('Segoe UI', 10),
                justify=tk.CENTER
            )
            instructions_label.pack(pady=10)
            
            # Add a text area to display the transcribed text
            self.transcript_area = scrolledtext.ScrolledText(
                self.microphone_window,
                wrap=tk.WORD,
                width=50,
                height=10,
                font=("Segoe UI", 10),
                state="disabled"
            )
            self.transcript_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            # Add buttons
            button_frame = ttk.Frame(self.microphone_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.listen_button = ttk.Button(
                button_frame, 
                text="Start Listening",
                command=self.toggle_listening
            )
            self.listen_button.pack(side=tk.LEFT, padx=5)
            
            insert_button = ttk.Button(
                button_frame, 
                text="Insert Text to Prompt",
                command=self.insert_transcript_to_prompt
            )
            insert_button.pack(side=tk.LEFT, padx=5)
            
            # Add "Send to Gemini" button
            send_to_gemini_button = ttk.Button(
                button_frame, 
                text="Send to Gemini",
                command=self.send_microphone_to_gemini
            )
            send_to_gemini_button.pack(side=tk.LEFT, padx=5)
            
            close_button = ttk.Button(
                button_frame, 
                text="Close",
                command=self.stop_listening
            )
            close_button.pack(side=tk.RIGHT, padx=5)
            
            self.update_status("Microphone ready")
            
        except MicrophoneError as e:
            logger.error(f"Microphone error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.update_status(f"Error initializing microphone: {str(e)}")
            if self.microphone_window:
                self.microphone_window.destroy()
                self.microphone_window = None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self.update_status(f"Error initializing microphone: {str(e)}")
            if self.microphone_window:
                self.microphone_window.destroy()
                self.microphone_window = None
    
    def toggle_listening(self):
        """Toggle between listening and not listening"""
        if self.listening:
            # Stop listening
            self.listening = False
            self.listen_button.config(text="Start Listening")
            self.update_status("Stopped listening")
        else:
            # Start listening
            self.listening = True
            self.listen_button.config(text="Stop Listening")
            self.update_status("Listening...")
            
            # Start listening in a separate thread
            self.listening_thread = threading.Thread(target=self.listen_for_speech)
            self.listening_thread.daemon = True
            self.listening_thread.start()
    
    def listen_for_speech(self):
        """Listen for speech and transcribe it"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                while self.listening:
                    try:
                        # Listen for audio
                        self.update_status("Listening to microphone...")
                        audio = self.recognizer.listen(source, timeout=5)
                        
                        # Recognize speech using Google Speech Recognition
                        self.update_status("Recognizing speech...")
                        text = self.recognizer.recognize_google(audio)
                        
                        # Add the transcribed text to the transcript area
                        self.update_transcript(text)
                        self.update_status("Speech recognized")
                    except sr.WaitTimeoutError:
                        # No speech detected
                        pass
                    except sr.UnknownValueError:
                        # Speech was unintelligible
                        self.update_status("Could not understand audio")
                    except sr.RequestError as e:
                        # Could not request results from Google Speech Recognition service
                        raise MicrophoneError(f"Error connecting to speech recognition service: {e}")
        except MicrophoneError as e:
            logger.error(f"Microphone error: {str(e)}")
            self.update_status(f"Error in speech recognition: {str(e)}")
            messagebox.showerror("Error", f"Error in speech recognition: {str(e)}")
            self.toggle_listening()  # Stop listening
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error in speech recognition: {str(e)}")
            messagebox.showerror("Error", f"Error in speech recognition: {str(e)}")
            self.toggle_listening()  # Stop listening
    
    def update_transcript(self, text):
        """Add text to the transcript area"""
        if not text:
            return
            
        self.audio_text += text + " "
        
        # Update the GUI in the main thread
        self.transcript_area.config(state="normal")
        self.transcript_area.delete("1.0", tk.END)
        self.transcript_area.insert(tk.END, self.audio_text)
        self.transcript_area.config(state="disabled")
        
        # Force the text area to scroll to the end
        self.transcript_area.see(tk.END)
    
    def insert_transcript_to_prompt(self):
        """Insert the transcribed text into the main prompt area"""
        if not self.audio_text:
            messagebox.showinfo("No Text", "There is no transcribed text to insert.")
            return
            
        # Insert the text into the input area
        current_text = self.input_area.get("1.0", tk.END).strip()
        if current_text:
            # If there's already text, add a space
            self.input_area.insert(tk.END, f" {self.audio_text}")
        else:
            # If the input area is empty, just insert the text
            self.input_area.insert("1.0", self.audio_text)
            
        self.update_status("Transcribed text inserted into prompt")
    
    def send_microphone_to_gemini(self):
        """Send the transcribed audio text to Gemini"""
        if not self.audio_text:
            messagebox.showinfo("No Text", "There is no transcribed text to send.")
            return
            
        try:
            # Update status
            self.update_status("Sending transcribed audio to Gemini...")
            
            # Add the audio text to the conversation history
            self.output_area.config(state="normal")
            self.output_area.insert(tk.END, f"\nYou: [Transcribed audio: \"{self.audio_text}\"]\n", "role")
            self.output_area.see(tk.END)
            self.output_area.config(state="disabled")
            
            # Send to Gemini
            self.send_to_gemini(self.audio_text)
            
            # Clear the transcribed text for next recording
            self.audio_text = ""
            self.transcript_area.config(state="normal")
            self.transcript_area.delete("1.0", tk.END)
            self.transcript_area.config(state="disabled")
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            self.update_status(f"Error sending audio transcript to Gemini: {str(e)}")
            messagebox.showerror("Error", f"Error sending audio transcript to Gemini: {str(e)}")
    
    def stop_listening(self):
        """Stop listening and close the microphone window"""
        if self.listening:
            self.listening = False
            
            # Wait for the listening thread to finish
            if self.listening_thread and self.listening_thread.is_alive():
                self.listening_thread.join(1.0)
        
        # Close the window
        if self.microphone_window:
            self.microphone_window.destroy()
            self.microphone_window = None
            
        self.update_status("Microphone closed")
    
    def about(self):
        """Handle the About menu item click"""
        messagebox.showinfo("About", "Gemini X - A custom Gemini interface")
        self.update_status("Gemini X - A custom Gemini interface")

    def on_closing(self):
        """Clean up resources before closing the application"""
        # Close the webcam if it's open
        self.close_webcam()
        
        # Close the screenshare if it's open
        self.close_screenshare()
        
        # Stop listening if active
        self.stop_listening()
        
        # Close the application
        self.root.destroy()

def main():
    # Create the main window
    root = tk.Tk()
    
    # Create custom style to match Google AI Studio
    style = ttk.Style()
    style.configure("TFrame", background="#f8f9fa")
    style.configure("TLabel", background="#f8f9fa", font=('Segoe UI', 10))
    style.configure("TButton", background="#4285f4", font=('Segoe UI', 10))
    
    # Initialize the application
    app = GeminiXApp(root)
    
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()