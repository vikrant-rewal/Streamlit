import streamlit as st
import requests
import datetime
import json
import os
import time
from gtts import gTTS
import tempfile
from streamlit_mic_recorder import mic_recorder

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Mom's Prudence",
    page_icon="🥘",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 1. SETUP & CONSTANTS ---
MEMORY_FILE = "memory.json"
DEFAULT_PREFERENCES = {
    "dislikes": ["Mix Veg", "Broccoli", "Ghiya", "Bottle Gourd", "Idli", "Dosa", "Thalipeeth"],
    "diet": "Vegetarian"
}

# --- 2. CSS STYLING (Mobile & Audio) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Food Card */
    .food-card { 
        background: white; border-radius: 15px; overflow: hidden; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 15px; border: 1px solid #f0f0f0;
    }
    .food-img-container { 
        height: 180px; overflow: hidden; background-color: #eee; position: relative;
    }
    .food-img { width: 100%; height: 100%; object-fit: cover; }
    .food-details { padding: 15px; }
    .food-title { font-size: 1.1em; font-weight: 700; color: #2c3e50; margin-bottom: 5px; }
    .food-desc { font-size: 0.85em; color: #7f8c8d; line-height: 1.4; }
    .meal-badge { 
        position: absolute; top: 10px; left: 10px; background-color: rgba(255, 255, 255, 0.95); 
        color: #e74c3c; padding: 4px 12px; border-radius: 20px; font-size: 0.75em; 
        font-weight: bold; text-transform: uppercase; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Custom Date Buttons */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 10px; height: 60px; border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* Audio Player styling styling */
    .stAudio { margin-top: 10px; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS (Memory & Images) ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    return DEFAULT_PREFERENCES

def save_memory(prefs):
    with open(MEMORY_FILE, "w") as f: json.dump(prefs, f)

def get_food_image_url(dish_name):
    # Reliable AI Generator endpoint with strict vegetarian prompt
    clean_name = dish_name.split('+')[0].strip()
    # We add a timestamp seed to ensure a fresh image try if one fails, but keep the prompt strict
    seed = int(time.time())
    prompt = f"vegetarian indian food dish {clean_name}, delicious, authentic, cinematic lighting, no meat"
    encoded_prompt = prompt.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=400&height=300&nologo=true&seed={seed}"

# --- 4. AUDIO FUNCTIONS (NEW) ---
def text_to_speech(menu_json):
    # 1. Create the script to read
    date_str = st.session_state.selected_date.strftime("%A, %d %B")
    speech_text = f"Here is the meal plan for {date_str}. "
    speech_text += f"For Breakfast: {menu_json.get('breakfast', {}).get('dish', 'something nice')}. "
    speech_text += f"For Lunch: {menu_json.get('lunch', {}).get('dish', 'a good meal')}. "
    speech_text += f"And for Dinner: {menu_json.get('dinner', {}).get('dish', 'a light dinner')}. "
    if menu_json.get('message'):
        speech_text += f"Note: {menu_json['message']}"

    # 2. Generate MP3 using Google TTS
    try:
        tts = gTTS(text=speech_text, lang='en', tld='co.in') # 'co.in' gives an Indian accent
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

# --- 5. THE ROBUST API CALL ---
def call_gemini_direct(prompt_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    models_waterfall = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-flash-latest"]
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    for model in models_waterfall:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            elif response.status_code in [429, 503]:
                time.sleep(1)
                continue
        except: continue
    st.error("⚠️ Mom's Chef is unreachable right now. Please try again in a minute.")
    return None

# --- 6. APP LOGIC & STATE ---
if 'preferences' not in st.session_state: st.session_state.preferences = load_memory()
if 'meal_plans' not in st.session_state: st.session_state.meal_plans = {} 
if 'selected_date' not in st.session_state: st.session_state.selected_date = datetime.date.today()

# Sidebar
with st.sidebar:
    st.header("🧠 Chef's Memory")
    st.write("I avoid these:")
    st.info(", ".join(st.session_state.preferences["dislikes"]))
    new_dislike = st.text_input("Add a dislike:")
    if st.button("Remember this"):
        if new_dislike and new_dislike not in st.session_state.preferences["dislikes"]:
            st.session_state.preferences["dislikes"].append(new_dislike)
            save_memory(st.session_state.preferences)
            st.rerun()

# --- 7. MAIN UI ---
st.markdown("### 🥘 Mom's Prudence")

# Calendar Strip
cols = st.columns(5)
today = datetime.date.today()
for i in range(5):
    day_date = today + datetime.timedelta(days=i)
    date_key = str(day_date)
    btn_type = "primary" if (day_date == st.session_state.selected_date) else "secondary"
    with cols[i]:
        if st.button(f"{day_date.strftime('%a')}\n{day_date.strftime('%d')}", key=f"btn_{date_key}", type=btn_type, use_container_width=True):
            st.session_state.selected_date = day_date
            st.rerun()
st.markdown("---")

# Display Logic
selected_date_str = str(st.session_state.selected_date)
current_menu = st.session_state.meal_plans.get(selected_date_str)

def generate_menu_ai():
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    is_weekend = st.session_state.selected_date.weekday() >= 5
    date_display = st.session_state.selected_date.strftime("%A, %d %b")
    prompt = f"""
    You are a smart family cook for 3 vegetarians in Mumbai. 
    STRICT CONSTRAINTS: 1. Diet: Vegetarian. NO Meat, NO Eggs. 2. AVOID: {dislikes}. 3. NO South Indian. 4. STYLE: Home-cooked North Indian/Mumbai. 
    CONTEXT: Planning for: {date_display}. Weekend Mode: {"YES" if is_weekend else "NO"}
    TASK: Generate JSON for Breakfast, Lunch, Dinner.
    OUTPUT JSON FORMAT: {{ "breakfast": {{ "dish": "Name", "desc": "Short description", "calories": "kcal" }}, "lunch": {{ "dish": "Name", "desc": "Short description", "calories": "kcal" }}, "dinner": {{ "dish": "Name", "desc": "Short description", "calories": "kcal" }}, "message": "Note" }}
    """
    with st.spinner(f"Planning meals for {date_display}..."):
        text_resp = call_gemini_direct(prompt)
        if text_resp:
            try: return json.loads(text_resp.replace("```json", "").replace("```", "").strip())
            except: st.error("Chef's handwriting was messy. Try again.")
        return None

if not current_menu:
    if st.button("✨ Plan This Day", type="primary", use_container_width=True):
        menu_data = generate_menu_ai()
        if menu_data:
            st.session_state.meal_plans[selected_date_str] = menu_data
            st.rerun()
else:
    # RENDER MENU
    def render_card(meal_type, data):
        dish_name = data.get('dish', 'Food')
        image_url = get_food_image_url(dish_name)
        st.markdown(f"""<div class="food-card"><div class="food-img-container"><img src="{image_url}" class="food-img" loading="lazy"><span class="meal-badge">{meal_type}</span></div><div class="food-details"><div class="food-title">{dish_name}</div><div class="food-desc">{data.get('desc', '')}</div><div style="margin-top: 10px; font-size: 0.8em; color: #888;">🔥 {data.get('calories', 'N/A')} • 🌿 Veg</div></div></div>""", unsafe_allow_html=True)

    render_card("Breakfast", current_menu.get('breakfast', {}))
    render_card("Lunch", current_menu.get('lunch', {}))
    render_card("Dinner", current_menu.get('dinner', {}))
    if "message" in current_menu: st.info(f"💡 {current_menu['message']}")

    # AUDIO PLAYER BUTTON
    if st.button("🔊 Listen to Menu", use_container_width=True):
        with st.spinner("Generating audio..."):
            audio_file = text_to_speech(current_menu)
            if audio_file:
                st.audio(audio_file, format='audio/mp3', start_time=0)

    if st.button("🔄 Regenerate Menu", use_container_width=True):
        menu_data = generate_menu_ai()
        if menu_data:
            st.session_state.meal_plans[selected_date_str] = menu_data
            st.rerun()

st.markdown("### 🗣️ Talk to the Chef")

# AUDIO INPUT & TEXT INPUT
c1, c2 = st.columns([1, 4])
with c1:
    # Microphone button
    audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key='recorder')
with c2:
    # Standard text input
    text_input = st.chat_input("Type your request here...")

# Determine final input source
final_feedback = None
if audio_input:
    # Only try to transcribe if audio was actually recorded
    with st.spinner("Transcribing speech..."):
        # Simple transcription via Gemini (since we already have the setup)
        # We send the raw bytes to Gemini for transcription
        try:
            model = "gemini-2.5-flash" # Use a fast model for transcription
            api_key = st.secrets["GEMINI_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            # We convert audio bytes to a string representation for the prompt
            # Note: A dedicated speech-to-text API is usually better, but this works for simple prototyping with existing keys.
            prompt_text = f"Transcribe the following user request regarding food: {str(audio_input['bytes'][:100])}... (audio data truncated for brevity, assume user said: 'Change lunch to something spicy')"
            # Ideally you would send audio bytes, but for simplicity in this setup we'll rely on text fallback or simulate transcription.
            # Given the constraints, let's stick to text input for reliability until a dedicated STT service is configured.
            st.warning("Real-time audio transcription requires a dedicated Speech-to-Text API setup. Please use the text box for now.")
        except:
             st.error("Audio processing failed.")

if text_input and current_menu:
    final_feedback = text_input

# Process Feedback
if final_feedback and current_menu:
    with st.spinner("Adjusting menu..."):
        current_menu_json = json.dumps(current_menu)
        prompt = f"Update this menu: {current_menu_json}. User Request: {final_feedback}. Output valid JSON only."
        text_response = call_gemini_direct(prompt)
        if text_response:
            try:
                clean_json = text_response.replace("```json", "").replace("```", "").strip()
                new_data = json.loads(clean_json)
                st.session_state.meal_plans[selected_date_str] = new_data
                st.rerun()
            except: st.error("Could not understand the update.")
