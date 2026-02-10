import { GoogleGenAI, Type } from "@google/genai";
import { SYSTEM_INSTRUCTION } from "../constants";

const getAiClient = () => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_API_KEY;

  if (!apiKey) {
    throw new Error("API Key is missing");
  }
  return new GoogleGenAI({ apiKey });
};

export const generateDailyMenu = async (isWeekend: boolean, history: string[], preferences: string): Promise<string> => {
  const ai = getAiClient();
  
  const today = new Date().toLocaleDateString('en-IN', { weekday: 'long' });
  
  const historyText = history.length > 0 
    ? history.map((m, i) => `Day -${history.length - i}: ${m.replace(/\n/g, '; ')}`).join('\n')
    : "No recent history.";

  const prompt = `
    Today is ${today}.
    Is it the weekend? ${isWeekend ? "Yes" : "No"}.
    
    ### USER PREFERENCES & DISLIKES (STRICTLY ADHERE TO THESE):
    ${preferences || "None specified."}

    ### RECENT MEAL HISTORY (DO NOT REPEAT DISHES FROM HERE):
    ${historyText}
    
    Please generate a fresh, non-repetitive menu for today.
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        temperature: 0.7,
      }
    });
    
    return response.text || "Sorry, I couldn't generate a menu at this time.";
  } catch (error) {
    console.error("Error generating menu:", error);
    return "Error generating menu. Please check your connection or API key.";
  }
};

export const updateMenuWithFeedback = async (
  currentMenu: string, 
  feedback: string, 
  isWeekend: boolean
): Promise<string> => {
  const ai = getAiClient();
  
  const prompt = `
    This is the current menu you generated:
    ---
    ${currentMenu}
    ---
    
    The user has feedback: "${feedback}".
    
    Please update the menu to address this feedback while keeping the other items the same if they weren't complained about.
    Remember the context: Is it weekend? ${isWeekend ? "Yes" : "No"}.
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
      }
    });
    
    return response.text || "Sorry, I couldn't update the menu.";
  } catch (error) {
    console.error("Error updating menu:", error);
    return "Error updating menu. Please try again.";
  }
};

export const extractDietaryConstraints = async (feedback: string): Promise<string[]> => {
  const ai = getAiClient();
  
  const prompt = `
    Analyze the following user feedback regarding food: "${feedback}".
    
    Identify if the user is expressing a PERMANENT dislike, restriction, or preference (e.g., "I hate broccoli", "No spice ever", "I'm vegan now", "Don't use mushrooms").
    Ignore temporary moods (e.g., "Not feeling like rice today", "Change dinner").
    
    Return a list of short constraint strings (e.g. "No broccoli", "Low spice"). 
    If none found, return an empty list.
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            constraints: {
              type: Type.ARRAY,
              items: { type: Type.STRING }
            }
          }
        }
      }
    });

    const result = JSON.parse(response.text || "{ \"constraints\": [] }");
    return result.constraints || [];
  } catch (error) {
    console.error("Error extracting constraints:", error);
    return [];
  }
};
