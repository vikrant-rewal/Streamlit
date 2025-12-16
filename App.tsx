import React, { useState, useEffect } from 'react';
import { Settings, Send, RefreshCw, MessageCircle, Trash2, BrainCircuit } from 'lucide-react';
import { Header } from './components/Header';
import { SettingsPanel } from './components/SettingsPanel';
import { Spinner } from './components/Spinner';
import { VoiceRecorder } from './components/VoiceRecorder';
import { generateDailyMenu, updateMenuWithFeedback, extractDietaryConstraints } from './services/gemini';

const MAX_HISTORY_ITEMS = 5;

const App: React.FC = () => {
  const [isWeekend, setIsWeekend] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [menu, setMenu] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  
  // History & Preferences state
  const [history, setHistory] = useState<string[]>([]);
  const [preferences, setPreferences] = useState<string>("");
  const [learningMessage, setLearningMessage] = useState<string | null>(null);

  // Load data from local storage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('meal_planner_history');
    if (savedHistory) setHistory(JSON.parse(savedHistory));

    const savedPrefs = localStorage.getItem('meal_planner_preferences');
    if (savedPrefs) setPreferences(savedPrefs);
  }, []);

  // Save preferences whenever they change
  useEffect(() => {
    localStorage.setItem('meal_planner_preferences', preferences);
  }, [preferences]);

  const saveToHistory = (newMenu: string) => {
    const updatedHistory = [newMenu, ...history].slice(0, MAX_HISTORY_ITEMS);
    setHistory(updatedHistory);
    localStorage.setItem('meal_planner_history', JSON.stringify(updatedHistory));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('meal_planner_history');
    setMenu(null);
  };

  const handleGenerateMenu = async () => {
    setIsLoading(true);
    try {
      const generatedMenu = await generateDailyMenu(isWeekend, history, preferences);
      setMenu(generatedMenu);
      setFeedback(''); 
      saveToHistory(generatedMenu);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateMenu = async () => {
    if (!menu || !feedback.trim()) return;
    
    setIsUpdating(true);
    setLearningMessage(null);

    try {
      // 1. Update the menu based on feedback
      const updatedMenuPromise = updateMenuWithFeedback(menu, feedback, isWeekend);
      
      // 2. In parallel, check if we learned any new preferences
      const extractionPromise = extractDietaryConstraints(feedback);

      const [updatedMenu, newConstraints] = await Promise.all([updatedMenuPromise, extractionPromise]);

      setMenu(updatedMenu);
      setFeedback('');
      saveToHistory(updatedMenu);

      // 3. Update preferences if new constraints were found
      if (newConstraints.length > 0) {
        const uniqueConstraints = new Set([
          ...preferences.split(',').map(s => s.trim()).filter(Boolean),
          ...newConstraints
        ]);
        setPreferences(Array.from(uniqueConstraints).join(', '));
        setLearningMessage(`Learned new preference: ${newConstraints.join(', ')}`);
        
        // Hide learning message after 3 seconds
        setTimeout(() => setLearningMessage(null), 3000);
      }

    } catch (error) {
      console.error(error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleVoiceTranscript = (text: string) => {
    setFeedback((prev) => (prev ? `${prev} ${text}` : text));
  };

  return (
    <div className="min-h-screen pb-12">
      <Header />
      
      {/* Mobile Settings Toggle */}
      <button 
        onClick={() => setIsSettingsOpen(true)}
        className="fixed top-4 left-4 z-30 p-2 bg-white rounded-full shadow-md text-gray-600 hover:text-orange-500 transition-colors md:hidden"
      >
        <Settings size={24} />
      </button>

      {/* Desktop Settings Toggle */}
      <div className="hidden md:block fixed top-6 left-6 z-30">
        <button 
          onClick={() => setIsSettingsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-md text-gray-700 hover:text-orange-500 transition-colors font-medium"
        >
          <Settings size={18} />
          Settings
        </button>
      </div>

      <SettingsPanel 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        isWeekend={isWeekend}
        setIsWeekend={setIsWeekend}
        preferences={preferences}
        setPreferences={setPreferences}
      />

      <main className="container mx-auto px-4 max-w-2xl">
        
        {/* Main Action Area */}
        {!menu && !isLoading && (
          <div className="flex flex-col items-center justify-center mt-12 text-center space-y-6">
            <div className="bg-orange-100 p-6 rounded-full">
              <span className="text-6xl">🍛</span>
            </div>
            <h2 className="text-2xl font-semibold text-gray-800">Hungry? Let's plan the day!</h2>
            <p className="text-gray-600 max-w-md">
              Get a customized vegetarian menu for breakfast, lunch, and dinner.
              <br/>
              <span className="text-xs text-gray-400 mt-2 block">
                Memory: {history.length > 0 ? `Tracking last ${history.length} menus.` : "Fresh start."}
                {preferences && <span className="block mt-1 text-orange-400">Following {preferences.split(',').length} preferences.</span>}
              </span>
              {isWeekend && <span className="block mt-2 text-orange-600 font-medium">✨ Weekend Mode Active</span>}
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleGenerateMenu}
                className="px-8 py-4 bg-orange-500 hover:bg-orange-600 text-white rounded-xl shadow-lg transform transition-all hover:-translate-y-1 font-bold text-lg flex items-center gap-2"
              >
                <RefreshCw size={20} />
                Generate Menu
              </button>
            </div>
            {history.length > 0 && (
              <button onClick={clearHistory} className="text-xs text-red-400 hover:text-red-600 flex items-center gap-1">
                <Trash2 size={12} /> Forget History
              </button>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center mt-20 space-y-4">
            <Spinner />
            <p className="text-gray-500 animate-pulse">Checking pantry & preferences...</p>
          </div>
        )}

        {/* Menu Display */}
        {menu && !isLoading && (
          <div className="animate-fade-in-up">
            <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-orange-100">
              <div className="bg-orange-50 p-4 border-b border-orange-100 flex justify-between items-center">
                <h3 className="font-bold text-orange-800 flex items-center gap-2">
                  <span className="text-xl">📅</span> Today's Plan
                </h3>
                {isWeekend && (
                  <span className="bg-orange-200 text-orange-800 text-xs px-2 py-1 rounded-full font-bold">
                    Weekend
                  </span>
                )}
              </div>
              
              <div className="p-6 md:p-8">
                <div className="prose prose-orange max-w-none text-gray-700 whitespace-pre-wrap font-medium text-lg leading-relaxed">
                  {menu}
                </div>
              </div>

              {/* Action Footer */}
              <div className="bg-gray-50 p-4 flex justify-end border-t border-gray-100">
                 <button
                  onClick={handleGenerateMenu}
                  className="text-gray-500 hover:text-orange-600 text-sm font-medium flex items-center gap-1 transition-colors"
                >
                  <RefreshCw size={14} />
                  Regenerate All
                </button>
              </div>
            </div>

            {/* Talk Back Feature */}
            <div className="mt-8 bg-white rounded-2xl shadow-lg p-6 border border-gray-100 relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-gray-800 font-semibold">
                  <MessageCircle className="text-orange-500" size={20} />
                  <h3>Talk Back to the Chef</h3>
                </div>
                {learningMessage && (
                   <div className="flex items-center gap-1 text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full animate-pulse">
                     <BrainCircuit size={12} />
                     {learningMessage}
                   </div>
                )}
              </div>
              
              <div className="relative">
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder={isListening ? "Listening..." : "Tell the chef what to change. Mention things like 'I hate broccoli' to remember forever."}
                  className={`w-full bg-gray-50 border rounded-xl p-4 pr-12 text-gray-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all resize-none h-24 ${isListening ? 'border-red-400 ring-2 ring-red-100' : 'border-gray-200'}`}
                />
                
                {/* Voice & Send Controls */}
                <div className="absolute bottom-3 right-3 flex items-center gap-2">
                   <VoiceRecorder 
                     onTranscript={handleVoiceTranscript} 
                     isListening={isListening}
                     setIsListening={setIsListening}
                   />

                  <button
                    onClick={handleUpdateMenu}
                    disabled={!feedback.trim() || isUpdating}
                    className={`p-2 rounded-lg transition-colors ${
                      feedback.trim() && !isUpdating
                        ? 'bg-orange-500 text-white hover:bg-orange-600' 
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {isUpdating ? (
                       <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <Send size={20} />
                    )}
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-2 ml-1">
                Preferences are automatically learned from your feedback. Check Settings to edit.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
