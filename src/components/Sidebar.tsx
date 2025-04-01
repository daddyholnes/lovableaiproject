
import { RefObject } from "react";
import { Button } from "@/components/ui/button";
import { Camera, CameraOff } from "lucide-react";

interface SidebarProps {
  videoRef: RefObject<HTMLVideoElement>;
  isCameraEnabled: boolean;
}

const Sidebar = ({ videoRef, isCameraEnabled }: SidebarProps) => {
  return (
    <div className="w-72 bg-gray-50 border-r border-gray-200 flex flex-col h-screen">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-medium text-gray-500 flex justify-between items-center">
          Webcam
          {isCameraEnabled ? <Camera size={18} /> : <CameraOff size={18} />}
        </h2>
        <div className="mt-3 flex flex-col items-center">
          <div className="relative w-full aspect-[4/3] rounded-lg bg-gray-100 overflow-hidden">
            {isCameraEnabled ? (
              <video 
                ref={videoRef}
                autoPlay 
                playsInline
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <CameraOff size={24} />
              </div>
            )}
          </div>
          <Button 
            variant="outline" 
            className="mt-3 w-full"
            disabled={!isCameraEnabled}
          >
            Capture
          </Button>
        </div>
      </div>
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-medium text-gray-500">Microphone</h2>
        <div className="mt-3">
          {/* Microphone visual representation could go here */}
          <div className="h-10 flex items-center justify-center bg-gray-100 rounded-md">
            <div className="w-6 h-6 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" className="text-gray-500">
                <path d="M480-160q-75 0-127.5-52.5T300-340v-280q0-75 52.5-127.5T480-800q75 0 127.5 52.5T660-620v280q0 75-52.5 127.5T480-160Zm0-480q33 0 56.5-23.5T560-680v-80q0-33-23.5-56.5T480-840q-33 0-56.5 23.5T400-760v80q0 33 23.5 56.5T480-440Zm0 320q100 0 170-70t70-170v-280q0-100-70-170t-170-70q-100 0-170 70t-70 170v280q0 100 70 170t170 70Zm0-320Z"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
