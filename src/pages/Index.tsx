
import { useState, useRef, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import SettingsSidebar from "@/components/SettingsSidebar";
import MediaControls from "@/components/MediaControls";
import Header from "@/components/Header";
import { useToast } from "@/hooks/use-toast";
import { io } from "socket.io-client";

const Index = () => {
  const [messages, setMessages] = useState<Array<{role: string; content: string; image?: string}>>([]);
  const [isCameraEnabled, setIsCameraEnabled] = useState<boolean>(true);
  const [isMicEnabled, setIsMicEnabled] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isPersonalMode, setIsPersonalMode] = useState<boolean>(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const { toast } = useToast();
  const [socket, setSocket] = useState<any>(null);

  useEffect(() => {
    // Create a socket connection to handle messages
    const socketConnection = io("http://localhost:5000", {
      transports: ['polling', 'websocket'], // Try polling first, then websocket
      upgrade: true,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000
    });

    socketConnection.on("connect", () => {
      console.log("Connected to server from Index");
    });

    socketConnection.on("stream_response_chunk", (data) => {
      // Add AI response in chunks
      const lastMessage = messages[messages.length - 1];
      
      if (lastMessage && lastMessage.role === "ai") {
        // Update the last message
        setMessages(prevMessages => {
          const updatedMessages = [...prevMessages];
          updatedMessages[updatedMessages.length - 1] = {
            ...updatedMessages[updatedMessages.length - 1],
            content: updatedMessages[updatedMessages.length - 1].content + data.text
          };
          return updatedMessages;
        });
      } else {
        // Create a new AI message
        setMessages(prevMessages => [
          ...prevMessages,
          { role: "ai", content: data.text }
        ]);
      }
    });

    setSocket(socketConnection);

    return () => {
      socketConnection.disconnect();
    };
  }, []);

  const handleSendMessage = (message: string, image?: string) => {
    // Add user message
    const updatedMessages = [...messages, { role: "user", content: message, image }];
    setMessages(updatedMessages);
    
    // Send the message to the backend via socket
    if (socket && socket.connected) {
      socket.emit('send_message', {
        text: message,
        model: selectedModel || 'gemini-1.0-pro', // Default if none selected
        image_base64: image,
        history: [] // You may want to format chat history here
      });
    } else {
      toast({
        title: "Connection error",
        description: "Not connected to server. Please ensure your Flask backend is running.",
        variant: "destructive",
      });
    }
  };

  const toggleCamera = () => {
    if (isCameraEnabled) {
      // Turn off camera
      if (stream) {
        stream.getTracks().forEach(track => {
          if (track.kind === 'video') {
            track.stop();
          }
        });
      }
    } else {
      // Turn on camera
      startWebcam();
    }
    setIsCameraEnabled(!isCameraEnabled);
  };

  const startWebcam = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      console.error("Error accessing webcam:", error);
      toast({
        title: "Camera error",
        description: "Could not access your camera. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    // Start webcam when component mounts
    if (isCameraEnabled) {
      startWebcam();
    }
    
    // Cleanup function to stop all tracks when component unmounts
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div className="flex h-screen bg-white">
      {/* Left Sidebar */}
      <Sidebar 
        videoRef={videoRef} 
        isCameraEnabled={isCameraEnabled}
      />
      
      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header 
          isPersonalMode={isPersonalMode}
          setIsPersonalMode={setIsPersonalMode}
        />
        
        {/* Chat Messages */}
        <ChatArea 
          messages={messages} 
          onSendMessage={handleSendMessage}
          selectedModel={selectedModel}
          setSelectedModel={setSelectedModel}
        />
        
        {/* Media Controls - Fixed at bottom right */}
        <MediaControls 
          isCameraEnabled={isCameraEnabled}
          isMicEnabled={isMicEnabled}
          toggleCamera={toggleCamera}
          toggleMic={() => setIsMicEnabled(!isMicEnabled)}
        />
      </div>
      
      {/* Right Sidebar */}
      <SettingsSidebar />
    </div>
  );
};

export default Index;
