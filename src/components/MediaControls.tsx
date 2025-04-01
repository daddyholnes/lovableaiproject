
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Camera, CameraOff, Mic, MicOff, Upload, ScreenShare, Folder, Youtube, FileIcon } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { io } from "socket.io-client";

interface MediaControlsProps {
  isCameraEnabled: boolean;
  isMicEnabled: boolean;
  toggleCamera: () => void;
  toggleMic: () => void;
}

const MediaControls = ({ 
  isCameraEnabled, 
  isMicEnabled, 
  toggleCamera,
  toggleMic 
}: MediaControlsProps) => {
  const [showPopover, setShowPopover] = useState(false);
  const [socket, setSocket] = useState<any>(null);
  const { toast } = useToast();
  
  useEffect(() => {
    // Connect to your backend server
    // Change this URL to match your backend server address
    const socketConnection = io("http://localhost:5000");
    
    socketConnection.on("connect", () => {
      toast({
        title: "Connected to server",
        description: "Successfully connected to the AI Studio backend",
      });
    });
    
    socketConnection.on("connect_error", (error) => {
      console.error("Connection error:", error);
      toast({
        title: "Connection error",
        description: "Could not connect to the AI Studio backend",
        variant: "destructive",
      });
    });
    
    setSocket(socketConnection);
    
    return () => {
      socketConnection.disconnect();
    };
  }, [toast]);
  
  const handleFileUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*,video/*';
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files[0]) {
        const file = target.files[0];
        console.log("File selected:", file);
        
        if (socket && socket.connected) {
          // Convert file to base64
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64data = reader.result as string;
            // Send to backend
            socket.emit('send_message', {
              text: 'Sent Image',
              model: 'gemini-1.0-pro-vision',  // Adjust model as needed
              image_base64: base64data,
              history: []  // You may want to add chat history here
            });
            
            toast({
              title: "File uploaded",
              description: `${file.name} has been sent to the AI`,
            });
          };
          reader.readAsDataURL(file);
        } else {
          toast({
            title: "Connection error",
            description: "Not connected to server. Please check your backend connection.",
            variant: "destructive",
          });
        }
      }
    };
    input.click();
  };

  const handleScreenShare = () => {
    toast({
      title: "Screen sharing",
      description: "Screen sharing feature coming soon",
    });
  };

  const handleDriveUpload = () => {
    toast({
      title: "Google Drive",
      description: "Google Drive integration coming soon",
    });
  };

  const handleYoutubeUpload = () => {
    toast({
      title: "YouTube",
      description: "YouTube integration coming soon",
    });
  };

  const handleFilesUpload = () => {
    toast({
      title: "Files",
      description: "Files feature coming soon",
    });
  };

  return (
    <div className="fixed bottom-6 right-6 flex flex-col items-end">
      <Popover open={showPopover} onOpenChange={setShowPopover}>
        <PopoverTrigger asChild>
          <Button 
            className="h-12 w-12 rounded-full bg-primary shadow-lg mb-3"
            onClick={() => setShowPopover(!showPopover)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-72 p-3 flex flex-col gap-2" side="top">
          <h3 className="font-medium mb-2">Add to conversation</h3>
          
          <div className="grid grid-cols-4 gap-2">
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={handleFileUpload}
            >
              <Upload className="h-5 w-5 mb-1" />
              <span className="text-xs">Upload</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={toggleCamera}
            >
              {isCameraEnabled ? 
                <Camera className="h-5 w-5 mb-1" /> : 
                <CameraOff className="h-5 w-5 mb-1" />
              }
              <span className="text-xs">Camera</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={toggleMic}
            >
              {isMicEnabled ? 
                <Mic className="h-5 w-5 mb-1" /> : 
                <MicOff className="h-5 w-5 mb-1" />
              }
              <span className="text-xs">Mic</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={handleScreenShare}
            >
              <ScreenShare className="h-5 w-5 mb-1" />
              <span className="text-xs">Screen</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={handleDriveUpload}
            >
              <FileIcon className="h-5 w-5 mb-1" />
              <span className="text-xs">Drive</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={handleYoutubeUpload}
            >
              <Youtube className="h-5 w-5 mb-1" />
              <span className="text-xs">YouTube</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex flex-col items-center h-16 py-2"
              onClick={handleFilesUpload}
            >
              <Folder className="h-5 w-5 mb-1" />
              <span className="text-xs">Files</span>
            </Button>
          </div>
          
          <p className="text-xs text-muted-foreground mt-2">Add files, images, or media to enhance your conversation</p>
        </PopoverContent>
      </Popover>
      
      <div className="flex space-x-2">
        <Button
          variant="outline"
          className="h-10 w-10 rounded-full p-0"
          onClick={toggleCamera}
        >
          {isCameraEnabled ? <Camera className="h-5 w-5" /> : <CameraOff className="h-5 w-5" />}
        </Button>
        
        <Button
          variant="outline"
          className="h-10 w-10 rounded-full p-0"
          onClick={toggleMic}
        >
          {isMicEnabled ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
        </Button>
      </div>
    </div>
  );
};

export default MediaControls;
