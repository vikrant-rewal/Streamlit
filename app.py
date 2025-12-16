import streamlit as st
import requests
import datetime
import json
import os
import time
import base64
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

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Food Card */
    .food-card { 
        background: white; border-radius: 15px; overflow: hidden; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 15px; border: 1px solid #f0f0f0;
    }
    .food-img-container { 
        height: 180px; overflow: hidden; background-color: #f4f4f4; position: relative;
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
    
    /* Buttons & Audio */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 10px; height: 60px; border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stAudio { margin-top: 10px; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    return DEFAULT_PREFERENCES

def save_memory(prefs):
    with open(MEMORY_FILE, "w") as f: json.dump(prefs, f)

def get_food_image_url(dish_name):
    clean_name = dish_name.split('+')[0].strip()
    seed = int(time.time())
    prompt = f"authentic indian vegetarian food {clean_name}, delicious, cinematic lighting, 8k, no meat"
    encoded_prompt = prompt.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=400&height=300&nologo=true&seed={seed}"

# --- 4. AUDIO FUNCTIONS (Fixed) ---
def text_to_speech(menu_json):
    date_str = st.session_state.selected_date.strftime("%A, %d %B")
    speech_text = f"Here is the plan for {date_str}. "
    speech_text += f"Breakfast: {menu_json.get('breakfast', {}).get('dish', 'something nice')}. "
    speech_text += f"Lunch: {menu_json.get('lunch', {}).get('dish', 'a good meal')}. "
    speech_text += f"Dinner: {menu_json.get('dinner', {}).get('dish', 'a light dinner')}. "
    try:
        tts = gTTS(text=speech_text, lang='en', tld='co.in')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

def transcribe_audio(audio_bytes):
    # This function uses Gemini to "listen" to the audio file
    api_key = st.secrets["GEMINI_API_KEY"]
    model = "gemini-1.5-flash" # 1.5 Flash handles audio very well
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    # Encode audio to Base64
    b64_data = base64.b64encode(audio_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Listen to this audio and write down exactly what the user is asking for regarding their food/meal plan."},
                {
                    "inline_data": {
                        "mime_type": "audio/wav", 
                        "data": b64_data
                    }
                }
            ]
        }]
    }
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        st.error(f"Transcription Error: {e}")
    return None

# --- 5. ROBUST MENU GENERATION ---
def call_gemini_direct(prompt_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            elif response.status_code in [429, 503]:
                time.sleep(1); continue
        except: continue
    return None

# --- 6. APP STATE ---
if 'preferences' not in st.session_state: st.session_state.preferences = load_memory()
if 'meal_plans' not in st.session_state: st.session_state.meal_plans = {} 
if 'selected_date' not in st.session_state: st.session_state.selected_date = datetime.date.today()

# Sidebar
with st.sidebar:
    st.header("🧠 Memory")
    st.info(", ".join(st.session_state.preferences["dislikes"]))
    new_dislike = st.text_input("Add dislike:")
    if st.button("Save"):
        if new_dislike: 
            st.session_state.preferences["dislikes"].append(new_dislike)
            save_memory(st.session_state.preferences)
            st.rerun()

# --- 7. MAIN UI ---
st.markdown("### 🥘 Mom's Prudence")

# Calendar
cols = st.columns(5)
today = datetime.date.today()
for i in range(5):
    day_date = today + datetime.timedelta(days=i)
    d_key = str(day_date)
    b_type = "primary" if (day_date == st.session_state.selected_date) else "secondary"
    with cols[i]:
        if st.button(f"{day_date.strftime('%a')}\n{day_date.strftime('%d')}", key=f"b_{d_key}", type=b_type, use_container_width=True):
            st.session_state.selected_date = day_date
            st.rerun()
st.markdown("---")

# Menu Logic
selected_date_str = str(st.session_state.selected_date)
current_menu = st.session_state.meal_plans.get(selected_date_str)

def generate_menu():
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    prompt = f"""
    Act as a Mumbai family cook (Vegetarian). 
    Constraints: No meat/eggs. Avoid: {dislikes}. No South Indian.
    Context: {st.session_state.selected_date.strftime("%A, %d %b")}.
    Task: Create JSON menu (breakfast, lunch, dinner).
    Format: {{ "breakfast": {{ "dish": "...", "desc": "...", "calories": "..." }}, "lunch": {{...}}, "dinner": {{...}}, "message": "..." }}
    """
    with st.spinner("Planning..."):
        res = call_gemini_direct(prompt)
        if res:
            try: return json.loads(res.replace("```json", "").replace("```", "").strip())
            except: pass
    return None

if not current_menu:
    if st.button("✨ Plan This Day", type="primary", use_container_width=True):
        data = generate_menu()
        if data:
            st.session_state.meal_plans[selected_date_str] = data
            st.rerun()
else:
    # Render Cards
    for meal in ['breakfast', 'lunch', 'dinner']:
        data = current_menu.get(meal, {})
        img = get_food_image_url(data.get('dish', 'food'))
        st.markdown(f"""
        <div class="food-card">
            <div class="food-img-container"><img src="{img}" class="food-img" loading="lazy"><span class="meal-badge">{meal}</span></div>
            <div class="food-details">
                <div class="food-title">{data.get('dish','')}</div>
                <div class="food-desc">{data.get('desc','')}</div>
                <small>🔥 {data.get('calories','')} • 🌿 Veg</small>
            </div>
        </div>""", unsafe_allow_html=True)
    
    if st.button("🔊 Listen to Menu", use_container_width=True):
        audio_file = text_to_speech(current_menu)
        if audio_file: st.audio(audio_file, format='audio/mp3', start_time=0)
    
    if st.button("🔄 Regenerate", use_container_width=True):
        data = generate_menu()
        if data:
            st.session_state.meal_plans[selected_date_str] = data
            st.rerun()

st.markdown("### 🗣️ Talk to the Chef")
c1, c2 = st.columns([1,5])
with c1:
    audio_data = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key='mic')
with c2:
    text_data = st.chat_input("Or type here...")

final_input = None

if audio_data:
    with st.spinner("Listening..."):
        transcribed_text = transcribe_audio(audio_data['bytes'])
        if transcribed_text:
            st.success(f"You said: {transcribed_text}")
            final_input = transcribed_text
        else:
            st.error("Couldn't hear you clearly.")

if text_data:
    final_input = text_data

if final_input and current_menu:
    with st.spinner("Updating menu..."):
        prompt = f"Update this menu JSON: {json.dumps(current_menu)}. User wants: {final_input}. Return valid JSON."
        res = call_gemini_direct(prompt)
        if res:
            try:
                st.session_state.meal_plans[selected_date_str] = json.loads(res.replace("```json","").replace("```","").strip())
                st.rerun()
            except: st.error("Update failed.")
