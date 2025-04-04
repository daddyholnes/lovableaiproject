import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { io } from "socket.io-client";

interface ChatAreaProps {
  messages: Array<{role: string; content: string; image?: string}>;
  onSendMessage: (message: string, image?: string) => void;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
}

const ChatArea = ({ messages, onSendMessage, selectedModel, setSelectedModel }: ChatAreaProps) => {
  const [inputMessage, setInputMessage] = useState("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const [socketConnected, setSocketConnected] = useState(false);

  useEffect(() => {
    // Connect to your Flask backend with improved configuration
    const socket = io("http://localhost:5000", {
      transports: ['polling', 'websocket'], // Try polling first, then websocket
      upgrade: true,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000
    });
    
    // Connection status events
    socket.on('connect', () => {
      console.log('Connected to server from ChatArea');
      setSocketConnected(true);
      // Request available models from the server
      socket.emit("request_models");
    });
    
    socket.on('connect_error', (error) => {
      console.log('Connection error from ChatArea:', error);
      setSocketConnected(false);
    });
    
    socket.on('disconnect', () => {
      console.log('Disconnected from server in ChatArea');
      setSocketConnected(false);
    });
    
    // Listen for available models from server
    socket.on("available_models", (models) => {
      console.log("Available models:", models);
      setAvailableModels(models);
      
      // Set default model if none selected yet
      if (!selectedModel && models.length > 0) {
        setSelectedModel(models[0]);
      }
    });
    
    // Clean up on unmount
    return () => {
      socket.disconnect();
    };
  }, [selectedModel, setSelectedModel]);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      onSendMessage(inputMessage);
      setInputMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden p-4">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto mb-4 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <h1 className="text-4xl font-bold text-gray-700 mb-6">What will you build?</h1>
            <p className="text-lg text-gray-500">Chat with AI models to explore new ideas</p>
            {!socketConnected && (
              <div className="mt-4 p-3 bg-yellow-100 text-yellow-800 rounded-md">
                Not connected to backend server. Make sure your Flask server is running.
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`p-3 rounded-lg max-w-[80%] ${
                  message.role === "user" 
                    ? "ml-auto bg-blue-100 text-blue-900" 
                    : "mr-auto bg-gray-100 text-gray-900"
                }`}
              >
                {message.image && (
                  <img 
                    src={message.image} 
                    alt="User shared image" 
                    className="mb-2 rounded max-w-full max-h-64 object-contain"
                  />
                )}
                <p>{message.content}</p>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border border-gray-300 rounded-full flex items-end bg-white shadow-sm">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 px-4 py-2 resize-none outline-none rounded-l-full max-h-32 min-h-[44px]"
          placeholder="Enter your message..."
          rows={1}
          style={{ overflow: inputMessage ? 'auto' : 'hidden' }}
          disabled={!socketConnected}
        />
        <div className="flex items-center pr-2">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-[180px] border-0 focus:ring-0">
              <SelectValue placeholder="Select Model" />
            </SelectTrigger>
            <SelectContent className="max-h-80 overflow-y-auto">
              {availableModels.length > 0 ? (
                availableModels.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="gemini-1.0-pro">gemini-1.0-pro</SelectItem>
              )}
            </SelectContent>
          </Select>
          <Button 
            onClick={handleSendMessage} 
            className="ml-2 rounded-full h-10 w-10 p-0 flex items-center justify-center"
            disabled={!socketConnected || !inputMessage.trim()}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;
