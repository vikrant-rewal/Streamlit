import React from 'react';
import { Calendar, X, HeartOff } from 'lucide-react';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isWeekend: boolean;
  setIsWeekend: (value: boolean) => void;
  preferences: string;
  setPreferences: (value: string) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ 
  isOpen, 
  onClose, 
  isWeekend, 
  setIsWeekend,
  preferences,
  setPreferences
}) => {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full w-64 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6 h-full overflow-y-auto">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-xl font-bold text-gray-800">Settings</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              <X size={24} />
            </button>
          </div>

          <div className="space-y-8">
            {/* Weekend Mode */}
            <div className="flex items-start space-x-3">
              <Calendar className="text-orange-500 mt-1 flex-shrink-0" size={20} />
              <div>
                <label className="text-gray-700 font-medium block mb-2">Weekend Mode</label>
                <p className="text-xs text-gray-500 mb-3">
                  Check this on Sat/Sun to enable headcount reminders.
                </p>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="sr-only peer" 
                    checked={isWeekend}
                    onChange={(e) => setIsWeekend(e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-500"></div>
                  <span className="ml-3 text-sm font-medium text-gray-700">{isWeekend ? 'On' : 'Off'}</span>
                </label>
              </div>
            </div>

            {/* Preferences / Dislikes */}
            <div className="flex items-start space-x-3">
              <HeartOff className="text-red-500 mt-1 flex-shrink-0" size={20} />
              <div className="w-full">
                <label className="text-gray-700 font-medium block mb-2">Dislikes & Preferences</label>
                <p className="text-xs text-gray-500 mb-3">
                  Foods to avoid or permanent diet rules. You can type here or tell the chef (e.g., "I hate broccoli").
                </p>
                <textarea
                  value={preferences}
                  onChange={(e) => setPreferences(e.target.value)}
                  placeholder="e.g. No mix veg, Less oil, No mushrooms..."
                  className="w-full h-32 p-3 text-sm border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
