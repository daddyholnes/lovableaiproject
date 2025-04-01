
import { useState, useRef, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import SettingsSidebar from "@/components/SettingsSidebar";
import MediaControls from "@/components/MediaControls";
import Header from "@/components/Header";

const Index = () => {
  const [messages, setMessages] = useState<Array<{role: string; content: string; image?: string}>>([]);
  const [isCameraEnabled, setIsCameraEnabled] = useState<boolean>(true);
  const [isMicEnabled, setIsMicEnabled] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isPersonalMode, setIsPersonalMode] = useState<boolean>(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const handleSendMessage = (message: string, image?: string) => {
    // Add user message
    const updatedMessages = [...messages, { role: "user", content: message, image }];
    setMessages(updatedMessages);
    
    // In a real implementation, this would connect to your Flask backend
    // The actual response will now come from the socket connection in MediaControls.tsx
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
