import streamlit as st
import requests
import datetime
import json
import os
import time
from gtts import gTTS
import tempfile
from streamlit_mic_recorder import mic_recorder

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ammy's Choice",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. SETUP & CONSTANTS ---
MEMORY_FILE = "memory.json"
DEFAULT_PREFERENCES = {
    "dislikes": ["Mix Veg", "Broccoli", "Ghiya", "Bottle Gourd", "Idli", "Dosa", "Thalipeeth"],
    "diet": "Vegetarian"
}

# --- 3. CSS STYLING (The "Pretty" Part) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* Global Styles */
    .stApp {
        background-color: #FFF9F5; /* Very soft cream background */
        font-family: 'Poppins', sans-serif;
    }
    
    h1, h2, h3 { color: #2D3436; font-weight: 600; }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #FF6B6B;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 2px 2px 0px rgba(0,0,0,0.05);
    }
    .main-header p { color: #636E72; font-size: 1rem; }

    /* Food Card Styling */
    .food-card { 
        background: white; 
        border-radius: 20px; 
        overflow: hidden; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); 
        margin-bottom: 25px; 
        border: none;
        transition: transform 0.2s;
    }
    .food-card:hover { transform: translateY(-3px); }
    
    .food-img-container { 
        height: 200px; 
        overflow: hidden; 
        position: relative;
    }
    .food-img { width: 100%; height: 100%; object-fit: cover; }
    
    .meal-badge { 
        position: absolute; 
        top: 15px; 
        left: 15px; 
        background-color: #FF6B6B; 
        color: white; 
        padding: 5px 15px; 
        border-radius: 20px; 
        font-size: 0.75rem; 
        font-weight: 600; 
        letter-spacing: 0.5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .food-details { padding: 20px; }
    .food-title { 
        font-size: 1.2rem; 
        font-weight: 600; 
        color: #2D3436; 
        margin-bottom: 8px; 
    }
    .food-desc { 
        font-size: 0.9rem; 
        color: #636E72; 
        line-height: 1.5; 
    }
    .food-meta {
        margin-top: 15px; 
        padding-top: 15px;
        border-top: 1px dashed #eee;
        font-size: 0.8em; 
        color: #B2BEC3;
        display: flex;
        justify-content: space-between;
    }

    /* Button Override */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    /* Primary buttons (Plan This Day) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B6B 0%, #EE5253 100%);
        box-shadow: 0 4px 15px rgba(238, 82, 83, 0.4);
    }
    
    /* Input Fields */
    .stTextInput input { border-radius: 12px; border: 1px solid #dfe6e9; }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    return DEFAULT_PREFERENCES

def save_memory(prefs):
    with open(MEMORY_FILE, "w") as f: json.dump(prefs, f)

def get_food_image_url(dish_name):
    clean_name = dish_name.split('+')[0].strip()
    seed = int(time.time())
    # High-quality prompt for Pollinations
    prompt = f"vegetarian indian food dish {clean_name}, delicious, authentic, cinematic lighting, 4k, no meat"
    encoded_prompt = prompt.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=600&height=400&nologo=true&seed={seed}"

def text_to_speech(menu_json):
    date_str = st.session_state.selected_date.strftime("%A, %d %B")
    speech_text = f"Ammy's choice for {date_str}. "
    speech_text += f"Breakfast: {menu_json.get('breakfast', {}).get('dish')}. "
    speech_text += f"Lunch: {menu_json.get('lunch', {}).get('dish')}. "
    speech_text += f"Dinner: {menu_json.get('dinner', {}).get('dish')}. "
    if menu_json.get('message'): speech_text += f"Tip: {menu_json['message']}"

    try:
        tts = gTTS(text=speech_text, lang='en', tld='co.in')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

# --- 5. ROBUST API CALL (Original Models Retained) ---
def call_gemini_direct(prompt_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # RETAINED AS PER USER REQUEST
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
    return None

# --- 6. STATE & SIDEBAR ---
if 'preferences' not in st.session_state: st.session_state.preferences = load_memory()
if 'meal_plans' not in st.session_state: st.session_state.meal_plans = {} 
if 'selected_date' not in st.session_state: st.session_state.selected_date = datetime.date.today()

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.write("**Dietary Restrictions**")
    st.warning("No: " + ", ".join(st.session_state.preferences["dislikes"]))
    new_dislike = st.text_input("Add restriction:")
    if st.button("Save Restriction"):
        if new_dislike:
            st.session_state.preferences["dislikes"].append(new_dislike)
            save_memory(st.session_state.preferences)
            st.rerun()

# --- 7. MAIN UI ---
# Header
st.markdown("<div class='main-header'><h1>🍳 Ammy's Choice</h1><p>Home-cooked meal planning, made simple.</p></div>", unsafe_allow_html=True)

# Date Selection
cols = st.columns(5)
today = datetime.date.today()
for i in range(5):
    day_date = today + datetime.timedelta(days=i)
    date_key = str(day_date)
    is_selected = (day_date == st.session_state.selected_date)
    btn_type = "primary" if is_selected else "secondary"
    
    with cols[i]:
        label = f"{day_date.strftime('%a')}\n{day_date.strftime('%d')}"
        if st.button(label, key=f"btn_{date_key}", type=btn_type, use_container_width=True):
            st.session_state.selected_date = day_date
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Main Logic
selected_date_str = str(st.session_state.selected_date)
current_menu = st.session_state.meal_plans.get(selected_date_str)

def generate_menu_ai():
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    is_weekend = st.session_state.selected_date.weekday() >= 5
    
    # --- LOGIC: Look back 5 days for repetition ---
    past_dishes = []
    for i in range(1, 6):
        prev = st.session_state.selected_date - datetime.timedelta(days=i)
        if str(prev) in st.session_state.meal_plans:
            p = st.session_state.meal_plans[str(prev)]
            for m in ['breakfast','lunch','dinner']: 
                if m in p: past_dishes.append(p[m].get('dish',''))
    
    past_str = ", ".join(list(set(filter(None, past_dishes)))) or "None"
    date_display = st.session_state.selected_date.strftime("%A, %d %b")

    prompt = f"""
    Role: Expert Vegetarian Indian Home Chef.
    Context: Planning meals for {date_display}. Weekend: {"Yes" if is_weekend else "No"}.
    Constraints: Vegetarian. NO {dislikes}. NO South Indian.
    Variety: RECENTLY EATEN: {past_str}. DO NOT REPEAT THESE. Use variety (Mushrooms, Corn, Soy, Kathal, etc).
    Output JSON: {{ "breakfast": {{ "dish": "", "desc": "", "calories": "" }}, "lunch": {{ "dish": "", "desc": "", "calories": "" }}, "dinner": {{ "dish": "", "desc": "", "calories": "" }}, "message": "Chef's Tip" }}
    """
    
    with st.spinner("🍳 Ammy is thinking..."):
        text_resp = call_gemini_direct(prompt)
        if text_resp:
            try: return json.loads(text_resp.replace("```json", "").replace("```", "").strip())
            except: st.error("Parsing error. Try again.")
        else: st.error("Ammy is unreachable. Check API Key or Models.")
        return None

if not current_menu:
    st.info(f"No plan for {st.session_state.selected_date.strftime('%A')}. Let's make one!")
    if st.button("✨ Create Menu", type="primary", use_container_width=True):
        menu_data = generate_menu_ai()
        if menu_data:
            st.session_state.meal_plans[selected_date_str] = menu_data
            st.rerun()
else:
    # Render Cards
    def render_card(meal, data):
        dish = data.get('dish', 'Unknown')
        img = get_food_image_url(dish)
        html = f"""
        <div class="food-card">
            <div class="food-img-container">
                <img src="{img}" class="food-img">
                <span class="meal-badge">{meal}</span>
            </div>
            <div class="food-details">
                <div class="food-title">{dish}</div>
                <div class="food-desc">{data.get('desc', '')}</div>
                <div class="food-meta">
                    <span>🔥 {data.get('calories', 'N/A')}</span>
                    <span>🌿 Vegetarian</span>
                </div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3) # Desktop grid, stacks on mobile
    with c1: render_card("Breakfast", current_menu.get('breakfast', {}))
    with c2: render_card("Lunch", current_menu.get('lunch', {}))
    with c3: render_card("Dinner", current_menu.get('dinner', {}))

    if "message" in current_menu:
        st.success(f"**Chef's Note:** {current_menu['message']}")

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🔊 Read Aloud", use_container_width=True):
            audio = text_to_speech(current_menu)
            if audio: st.audio(audio, format='audio/mp3', start_time=0)
    with c_btn2:
        if st.button("🔄 Shuffle Menu", use_container_width=True):
            menu_data = generate_menu_ai()
            if menu_data:
                st.session_state.meal_plans[selected_date_str] = menu_data
                st.rerun()

st.markdown("---")
st.markdown("### 💬 Ask Ammy")

# Action Bar
col_mic, col_text = st.columns([1, 5])
with col_mic:
    audio_blob = mic_recorder(start_prompt="🎙️", stop_prompt="🛑", key='mic')
with col_text:
    text_req = st.chat_input("Ex: Change dinner to something spicy...")

final_req = text_req
if audio_blob:
    st.toast("Audio received! (Transcription disabled in demo)")

if final_req and current_menu:
    with st.spinner("Adjusting recipe..."):
        # Quick update logic
        curr = json.dumps(current_menu)
        p = f"Update menu: {curr}. Request: {final_req}. Return strictly JSON."
        resp = call_gemini_direct(p)
        if resp:
            try:
                new_m = json.loads(resp.replace("```json", "").replace("```", "").strip())
                st.session_state.meal_plans[selected_date_str] = new_m
                st.rerun()
            except: st.error("Couldn't update.")
