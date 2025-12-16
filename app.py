import streamlit as st
import requests
import datetime
import json
import os
import time
import random
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

# Fun loading messages
LOADING_MESSAGES = [
    "🥕 Chopping the freshest vegetables...",
    "🍅 Simmering the sauces to perfection...",
    "🥬 Picking the best leaves from the garden...",
    "🌶️ Adding a pinch of magic spice...",
    "🍲 Consulting Grandma's secret recipe book...",
    "🥗 Calculating the perfect nutrition balance...",
    "👨‍🍳 The Chef is brainstorming your delicious day...",
    "🥑 Did you know? Healthy fats fuel your brain!",
    "🍋 Squeezing some zest into your life..."
]

# --- 3. CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* Global Styles */
    .stApp {
        background-color: #FFF9F5; 
        font-family: 'Poppins', sans-serif;
    }
    
    h1, h2, h3 { color: #2D3436; font-weight: 600; }
    
    /* Header */
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
    
    /* Food Card */
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
        background: #f0f0f0;
    }
    .food-img { width: 100%; height: 100%; object-fit: cover; }
    
    .meal-badge { 
        position: absolute; top: 15px; left: 15px; 
        background-color: #FF6B6B; color: white; 
        padding: 5px 15px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .food-details { padding: 20px; }
    .food-title { font-size: 1.2rem; font-weight: 600; color: #2D3436; margin-bottom: 8px; }
    .food-desc { font-size: 0.9rem; color: #636E72; line-height: 1.5; }
    .food-meta {
        margin-top: 15px; padding-top: 15px;
        border-top: 1px dashed #eee;
        font-size: 0.8em; color: #B2BEC3;
        display: flex; justify-content: space-between;
    }

    /* Ingredients Section */
    .ingredients-box {
        background-color: #fff;
        border: 2px dashed #FF6B6B;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
    }
    .ing-title {
        color: #FF6B6B; font-weight: 600; font-size: 1.1em; margin-bottom: 10px;
        display: flex; align-items: center; gap: 10px;
    }

    /* Custom Loading Animation Style */
    .chef-loading {
        text-align: center;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin: 20px 0;
    }
    .chef-loading-text {
        color: #FF6B6B;
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 15px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }

    /* UI Elements */
    div.stButton > button { border-radius: 12px; font-weight: 600; border: none; }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B6B 0%, #EE5253 100%);
        box-shadow: 0 4px 15px rgba(238, 82, 83, 0.4);
    }
    .stTextInput input { border-radius: 12px; }
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

# --- 5. GEMINI API FUNCTIONS ---

# A. Image Generation (Imagen)
def call_gemini_image_api(prompt_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    model = "imagen-3.0-generate-001"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
    headers = { "Content-Type": "application/json", "x-goog-api-key": api_key }
    payload = {
        "instances": [{ "prompt": prompt_text }],
        "parameters": { "aspectRatio": "4:3", "sampleCount": 1 }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['predictions'][0]['bytesBase64Encoded']
    except: pass
    return None

# B. Text Generation (Standard)
def call_gemini_text_api(prompt_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    # Retained your specific model list
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

# C. Cached Image Wrapper
@st.cache_data(show_spinner=False, ttl=3600*24)
def get_food_image_data(dish_name):
    if not dish_name or dish_name == 'Unknown':
        return "https://via.placeholder.com/600x400?text=No+Dish+Selected"
    
    clean_name = dish_name.split('+')[0].strip()
    prompt = f"A delicious, professional food photography shot of vegetarian Indian dish {clean_name}, served in an authentic bowl, cinematic lighting, highly detailed, 4k resolution."
    
    base64_data = call_gemini_image_api(prompt)
    if base64_data: return f"data:image/jpeg;base64,{base64_data}"
    return "https://via.placeholder.com/600x400?text=Image+Generation+Failed"

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
        if st.button(f"{day_date.strftime('%a')}\n{day_date.strftime('%d')}", key=f"btn_{date_key}", type=btn_type, use_container_width=True):
            st.session_state.selected_date = day_date
            st.rerun()
st.markdown("<br>", unsafe_allow_html=True)

selected_date_str = str(st.session_state.selected_date)
current_menu = st.session_state.meal_plans.get(selected_date_str)

def generate_menu_ai():
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    is_weekend = st.session_state.selected_date.weekday() >= 5
    
    # History Logic
    past_dishes = []
    for i in range(1, 6):
        prev = st.session_state.selected_date - datetime.timedelta(days=i)
        if str(prev) in st.session_state.meal_plans:
            p = st.session_state.meal_plans[str(prev)]
            for m in ['breakfast','lunch','dinner']: 
                if m in p: past_dishes.append(p[m].get('dish',''))
    past_str = ", ".join(list(set(filter(None, past_dishes)))) or "None"
    
    date_display = st.session_state.selected_date.strftime("%A, %d %b")

    # UPDATED PROMPT to ask for ingredients
    prompt = f"""
    Role: Expert Vegetarian Indian Home Chef.
    Context: Planning meals for {date_display}. Weekend: {"Yes" if is_weekend else "No"}.
    Constraints: Vegetarian. NO {dislikes}. NO South Indian.
    Variety: RECENTLY EATEN: {past_str}. DO NOT REPEAT THESE. Use variety (Mushrooms, Corn, Soy, Kathal, etc).
    
    TASK: Generate a menu AND a shopping list of main ingredients required for all 3 meals combined.
    
    Output JSON: {{ 
        "breakfast": {{ "dish": "", "desc": "", "calories": "" }}, 
        "lunch": {{ "dish": "", "desc": "", "calories": "" }}, 
        "dinner": {{ "dish": "", "desc": "", "calories": "" }}, 
        "message": "Chef's Tip",
        "ingredients": ["Item 1", "Item 2", "Item 3", "etc..."] 
    }}
    """
    
    # --- CUSTOM LOADING ANIMATION ---
    loading_placeholder = st.empty()
    random_msg = random.choice(LOADING_MESSAGES)
    
    # Display the animation
    loading_placeholder.markdown(f"""
        <div class="chef-loading">
            <div style="font-size: 3rem;">🥘</div>
            <div class="chef-loading-text">{random_msg}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Call API
    text_resp = call_gemini_text_api(prompt)
    
    # Clear animation
    loading_placeholder.empty()
    
    if text_resp:
        try: return json.loads(text_resp.replace("```json", "").replace("```", "").strip())
        except: st.error("Parsing error. Try again.")
    else: st.error("Ammy is unreachable. Check API Key.")
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
        img_src = get_food_image_data(dish)
        
        html = f"""
        <div class="food-card">
            <div class="food-img-container">
                <img src="{img_src}" class="food-img">
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

    # Use a spinner only for the images now, as the menu data is already loaded
    with st.spinner("Plating up the dishes (Generating Images)..."):
        c1, c2, c3 = st.columns(3)
        with c1: render_card("Breakfast", current_menu.get('breakfast', {}))
        with c2: render_card("Lunch", current_menu.get('lunch', {}))
        with c3: render_card("Dinner", current_menu.get('dinner', {}))

    if "message" in current_menu:
        st.success(f"**Chef's Note:** {current_menu['message']}")

    # --- INGREDIENTS SECTION (NEW) ---
    ingredients_list = current_menu.get('ingredients', [])
    if ingredients_list:
        st.markdown(f"""
        <div class="ingredients-box">
            <div class="ing-title">🛒 Ingredients for Today</div>
            <p style="color: #636E72; font-size: 0.9rem; margin-bottom: 10px;">Here is everything you need to cook these 3 meals:</p>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                {''.join([f'<span style="background:#FFF0F0; color:#E17055; padding:5px 10px; border-radius:15px; font-size:0.85em; border:1px solid #FAB1A0;">{item}</span>' for item in ingredients_list])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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
                st.cache_data.clear()
                st.rerun()

st.markdown("---")
st.markdown("### 💬 Ask Ammy")

col_mic, col_text = st.columns([1, 5])
with col_mic:
    audio_blob = mic_recorder(start_prompt="🎙️", stop_prompt="🛑", key='mic')
with col_text:
    text_req = st.chat_input("Ex: Change dinner to something spicy...")

if text_req and current_menu:
    with st.spinner("Adjusting recipe..."):
        curr = json.dumps(current_menu)
        p = f"Update menu: {curr}. Request: {text_req}. Return valid JSON with 'ingredients' list updated."
        resp = call_gemini_text_api(p)
        if resp:
            try:
                new_m = json.loads(resp.replace("```json", "").replace("```", "").strip())
                st.session_state.meal_plans[selected_date_str] = new_m
                st.cache_data.clear() 
                st.rerun()
            except: st.error("Couldn't update.")
