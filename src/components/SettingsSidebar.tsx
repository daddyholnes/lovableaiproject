
import { useState } from "react";
import { Button } from "@/components/ui/button";

const SettingsSidebar = () => {
  const [temperature, setTemperature] = useState(1);

  return (
    <div className="w-72 bg-white border-l border-gray-200 flex flex-col h-screen">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-base font-medium">Settings</h2>
      </div>
      
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-500 mb-3">Temperature</h3>
        <div className="flex items-center">
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full accent-blue-500"
          />
          <span className="ml-2 text-sm font-medium w-6">{temperature}</span>
        </div>
      </div>
      
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-500 mb-3">Advanced Settings</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Max output tokens</span>
            <input
              type="number"
              className="w-20 px-2 py-1 border rounded"
              defaultValue={1024}
              min={1}
              max={8192}
            />
          </div>
          <div className="flex items-center justify-between">
            <span>Top-K</span>
            <input
              type="number"
              className="w-20 px-2 py-1 border rounded"
              defaultValue={40}
              min={1}
              max={100}
            />
          </div>
          <div className="flex items-center justify-between">
            <span>Top-P</span>
            <input
              type="number"
              className="w-20 px-2 py-1 border rounded"
              defaultValue={0.95}
              min={0}
              max={1}
              step={0.01}
            />
          </div>
        </div>
      </div>
      
      <div className="p-4">
        <Button variant="outline" className="w-full">Reset Settings</Button>
      </div>
    </div>
  );
};

export default SettingsSidebar;
