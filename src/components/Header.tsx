
import { Button } from "@/components/ui/button";
import { User } from "lucide-react";

interface HeaderProps {
  isPersonalMode: boolean;
  setIsPersonalMode: (value: boolean) => void;
}

const Header = ({ isPersonalMode, setIsPersonalMode }: HeaderProps) => {
  return (
    <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
      <div className="flex items-center">
        <div className="text-xl font-medium flex items-center">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-6 w-6 mr-2" 
            viewBox="0 -960 960 960" 
            width="24"
          >
            <path d="M480-160q-75 0-127.5-52.5T300-340v-280q0-75 52.5-127.5T480-800q75 0 127.5 52.5T660-620v280q0 75-52.5 127.5T480-160Zm0-480q33 0 56.5-23.5T560-680v-80q0-33-23.5-56.5T480-840q-33 0-56.5 23.5T400-760v80q0 33 23.5 56.5T480-440Zm0 320q100 0 170-70t70-170v-280q0-100-70-170t-170-70q-100 0-170 70t-70 170v280q0 100 70 170t170 70Zm0-320Z"/>
          </svg>
          AI Studio
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <Button 
          variant={isPersonalMode ? "default" : "outline"} 
          className="flex items-center"
          onClick={() => setIsPersonalMode(!isPersonalMode)}
        >
          <User className="mr-2 h-4 w-4" />
          Personal
        </Button>
      </div>
    </div>
  );
};

export default Header;
