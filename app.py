import streamlit as st
import requests
import datetime
import json
import os
import time
import random
import re
from gtts import gTTS
import tempfile

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ammy's Choice",
    page_icon="🍳",
    layout="wide", # Changed to wide to utilize desktop space better
    initial_sidebar_state="collapsed"
)

# --- 2. SETUP & CONSTANTS ---
MEMORY_FILE = "memory.json"
DEFAULT_PREFERENCES = {
    "dislikes": ["Mix Veg", "Broccoli", "Ghiya", "Bottle Gourd", "Idli", "Dosa", "Thalipeeth"],
    "diet": "Vegetarian"
}

MEAL_IMAGES = {
    "breakfast": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    "lunch": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    "dinner": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    "default": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
}

LOADING_MESSAGES = [
    "🥕 Chopping the freshest Bhindi...",
    "🍅 Simmering the Channa Masala...",
    "🥬 Picking fresh Beans from the garden...",
    "👨‍🍳 Claude is preparing a rich Kofta gravy...",
    "🥑 Did you know? Chickpeas are packed with protein!",
    "🍋 Squeezing some zest into your life..."
]

# --- 3. CSS STYLING (The "Pretty" Part) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* GLOBAL APP STYLES */
    .stApp {
        background-color: #FFF9F5; /* Cream background */
        font-family: 'Poppins', sans-serif;
    }
    
    /* REMOVE DEFAULT STREAMLIT PADDING */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1000px; /* Keep content centered and readable on wide screens */
    }

    /* HEADER */
    .main-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .main-header h1 {
        color: #FF6B6B;
        font-weight: 700;
        font-size: 2.8rem;
        margin: 0;
        letter-spacing: -1px;
    }
    .main-header p {
        color: #888;
        font-size: 1rem;
        margin-top: 5px;
    }

    /* DATE BUTTONS */
    div.stButton > button[kind="secondary"] {
        background-color: white;
        border: 1px solid #eee;
        color: #555;
        border-radius: 15px;
        height: 3em;
        font-weight: 600;
        transition: all 0.2s;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B6B 0%, #EE5253 100%);
        color: white;
        border: none;
        border-radius: 15px;
        height: 3em;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(255, 107, 107, 0.3);
    }

    /* FOOD CARD CONTAINER */
    .food-card {
        background: white;
        border-radius: 20px 20px 0 0; /* Rounded top only */
        overflow: hidden;
        border: 1px solid #f0f0f0;
        border-bottom: none; /* Connect to button below */
        position: relative;
    }
    
    .food-img-container {
        height: 180px;
        overflow: hidden;
        position: relative;
    }
    .food-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s;
    }
    .food-card:hover .food-img {
        transform: scale(1.05);
    }
    
    .meal-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(255, 255, 255, 0.95);
        color: #FF6B6B;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .food-details {
        padding: 18px;
    }
    .food-title {
        color: #2D3436;
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.3;
        margin-bottom: 8px;
        min-height: 3rem; /* Align titles */
    }
    .food-desc {
        color: #636E72;
        font-size: 0.85rem;
        line-height: 1.5;
        min-height: 4.5rem; /* Align descriptions */
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .food-meta {
        margin-top: 15px;
        padding-top: 12px;
        border-top: 1px dashed #eee;
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: #B2BEC3;
        font-weight: 600;
    }

    /* INGREDIENTS SECTION */
    .ingredients-container {
        background: white;
        border-radius: 20px;
        padding: 25px;
        margin-top: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        text-align: center;
    }
    .ing-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2D3436;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .pill {
        display: inline-block;
        background: #FFF5F5;
        color: #FF6B6B;
        padding: 6px 14px;
        border-radius: 50px;
        font-size: 0.85rem;
        margin: 4px;
        border: 1px solid #FFE3E3;
        font-weight: 500;
    }

    /* ACTION BUTTONS (Bottom) */
    .action-btn-container {
        margin-top: 20px;
    }

    /* SWAP BUTTON STYLING (Specific Target) */
    /* We style the secondary buttons that appear inside columns */
    div[data-testid="column"] button[kind="secondary"] {
        border-radius: 0 0 20px 20px; /* Rounded bottom only */
        border-top: 1px solid #f0f0f0;
        margin-top: -5px; /* Pull closer to card */
        width: 100%;
        background-color: white;
        color: #FF6B6B;
        border-color: #f0f0f0;
    }
    div[data-testid="column"] button[kind="secondary"]:hover {
        background-color: #FFF5F5;
        border-color: #FF6B6B;
        color: #FF6B6B;
    }

    /* LOADING ANIMATION */
    .chef-loading {
        text-align: center;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        margin: 20px auto;
        max-width: 500px;
    }
    .chef-loading-text {
        color: #FF6B6B;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 15px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    
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
    speech_text = f"Hello! Here is the menu for {date_str}. "
    speech_text += f"Breakfast: {menu_json.get('breakfast', {}).get('dish')}. "
    speech_text += f"Lunch: {menu_json.get('lunch', {}).get('dish')}. "
    speech_text += f"Dinner: {menu_json.get('dinner', {}).get('dish')}. "
    if menu_json.get('message'): speech_text += f"Note: {menu_json['message']}"

    try:
        tts = gTTS(text=speech_text, lang='en', tld='co.in')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

def extract_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match: return json.loads(match.group())
        return json.loads(text)
    except: return None

# ==========================================
# --- 5. API FUNCTIONS ---
# ==========================================
def call_claude_api(prompt_text):
    try: api_key = st.secrets["CLAUDE_API_KEY"]
    except: return None
    url = "https://api.anthropic.com/v1/messages"
    headers = { "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json" }
    payload = { "model": "claude-3-5-haiku-20241022", "max_tokens": 1024, "messages": [{"role": "user", "content": prompt_text}] }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200: return response.json()['content'][0]['text']
        else: return None
    except: return None

def call_gemini_image_api(prompt_text):
    try: api_key = st.secrets["GEMINI_IMAGE_KEY"]
    except: return None
    model = "gemini-2.0-flash-exp-image-generation"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
    headers = { "Content-Type": "application/json", "x-goog-api-key": api_key }
    payload = { "instances": [{ "prompt": prompt_text, "parameters": {"aspectRatio": "4:3"} }] }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if 'predictions' in result and result['predictions']:
                 prediction = result['predictions'][0]
                 if 'bytesBase64Encoded' in prediction: return prediction['bytesBase64Encoded']
                 elif 'image' in prediction and 'b64' in prediction['image']: return prediction['image']['b64']
        return None
    except: return None

@st.cache_data(show_spinner=False, ttl=3600*24)
def get_food_image(dish_name):
    if not dish_name or dish_name == 'Food': return None
    clean_name = dish_name.split('+')[0].strip()
    prompt = f"A delicious, professional food photography shot of the vegetarian Indian dish '{clean_name}', served in an authentic bowl or plate. Cinematic lighting, high resolution, appetizing."
    base64_data = call_gemini_image_api(prompt)
    if base64_data: return f"data:image/jpeg;base64,{base64_data}"
    return None

# ==========================================
# --- 6. STATE & DATE LOGIC ---
# ==========================================
if 'preferences' not in st.session_state: st.session_state.preferences = load_memory()
if 'meal_plans' not in st.session_state: st.session_state.meal_plans = {} 

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
today_ist = datetime.datetime.now(IST).date()

if 'selected_date' not in st.session_state: st.session_state.selected_date = today_ist
if st.session_state.selected_date < today_ist: st.session_state.selected_date = today_ist

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Dietary Preferences")
    
    st.write("**Add a Dislike:**")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_dislike = st.text_input("New item", label_visibility="collapsed", placeholder="E.g. Mushroom")
    with col2:
        add_btn = st.button("➕", help="Add to list")

    if add_btn and new_dislike:
        if new_dislike not in st.session_state.preferences["dislikes"]:
            st.session_state.preferences["dislikes"].append(new_dislike)
            save_memory(st.session_state.preferences)
            st.rerun()
            
    st.write("---")
    st.write("**Your Restrictions:**")
    st.caption("Click the 'x' to remove an item.")
    current_list = st.session_state.preferences["dislikes"]
    updated_list = st.multiselect("Edit Restrictions", options=current_list, default=current_list, label_visibility="collapsed")
    
    if len(updated_list) < len(current_list):
        st.session_state.preferences["dislikes"] = updated_list
        save_memory(st.session_state.preferences)
        st.rerun()

# --- 7. MAIN UI ---
st.markdown("<div class='main-header'><h1>🍳 Ammy's Choice</h1><p>Home-cooked meal planning, made simple.</p></div>", unsafe_allow_html=True)

# DATE SELECTOR (Centered & Clean)
date_cols = st.columns([1,1,1,1,1])
for i in range(5):
    day_date = today_ist + datetime.timedelta(days=i)
    date_key = str(day_date)
    is_selected = (day_date == st.session_state.selected_date)
    btn_type = "primary" if is_selected else "secondary"
    with date_cols[i]:
        if st.button(f"{day_date.strftime('%a')}\n{day_date.strftime('%d')}", key=f"btn_{date_key}", type=btn_type, use_container_width=True):
            st.session_state.selected_date = day_date
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

selected_date_str = str(st.session_state.selected_date)
current_menu = st.session_state.meal_plans.get(selected_date_str)

# PLACEHOLDERS for Dynamic Interaction
action_placeholder = st.empty()

# --- REGENERATION LOGIC (SINGLE MEAL) ---
def regenerate_single_meal(meal_type, current_full_menu):
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    prompt = f"""
    You are a JSON-only API.
    CONTEXT: Current Menu: {json.dumps(current_full_menu)}.
    TASK: Change ONLY {meal_type} to a different vegetarian Indian dish.
    CONSTRAINTS: NO {dislikes}. Update 'ingredients' accordingly.
    RETURN ONLY VALID JSON.
    """
    with st.spinner(f"🍳 Whipping up a new {meal_type}..."):
        text_resp = call_claude_api(prompt)
        if text_resp:
            new_data = extract_json(text_resp)
            if new_data:
                st.session_state.meal_plans[selected_date_str] = new_data
                st.cache_data.clear()
                st.rerun()
            else: st.error("Chef got confused. Try again.")
        else: st.error("Chef is unreachable.")

def generate_menu_ai():
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    is_weekend = st.session_state.selected_date.weekday() >= 5
    
    # History check
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
    You are an expert Vegetarian Indian Home Chef.
    Context: Planning meals for {date_display}. Weekend: {"Yes" if is_weekend else "No"}.
    Constraints: Vegetarian. NO {dislikes}. NO South Indian (unless requested).
    
    VARIETY RULES:
    1. HISTORY: Recently eaten: {past_str}.
    2. PANEER RULE: If "Paneer" in history, NO Paneer for Dinner. Serve Soy Chaap, Malai Kofta, Rajma, Chole.
    3. FAVORITES: Rotate Bhindi, Channa, Rajma, Beans.
    
    TASK: Generate menu & shopping list.
    Output JSON ONLY: {{ "breakfast": {{...}}, "lunch": {{...}}, "dinner": {{...}}, "message": "...", "ingredients": [...] }}
    """
    
    action_placeholder.empty()
    random_msg = random.choice(LOADING_MESSAGES)
    with action_placeholder.container():
         st.markdown(f"""
            <div class="chef-loading">
                <div style="font-size: 3rem;">🥘</div>
                <div class="chef-loading-text">{random_msg}</div>
            </div>
        """, unsafe_allow_html=True)
    
    text_resp = call_claude_api(prompt)
    action_placeholder.empty()
    
    if text_resp:
        data = extract_json(text_resp)
        if data: return data
        st.error("Chef's handwriting was messy. Try again.")
    return None

if not current_menu:
    with action_placeholder.container():
        st.info(f"No plan for {st.session_state.selected_date.strftime('%A')}. Let's make one!")
        if st.button("✨ Create Menu", type="primary", use_container_width=True):
            menu_data = generate_menu_ai()
            if menu_data:
                st.session_state.meal_plans[selected_date_str] = menu_data
                st.rerun()
else:
    # --- RENDER MENU GRID ---
    # Using columns with 'medium' gap for breathing room
    c1, c2, c3 = st.columns(3, gap="medium")
    
    def render_card_with_action(col, meal_type, data):
        with col:
            dish_name = data.get('dish', 'Food')
            meal_key = meal_type.lower()
            
            with st.spinner(f"Loading..."):
                 ai_image_url = get_food_image(dish_name)
            final_image_url = ai_image_url if ai_image_url else MEAL_IMAGES.get(meal_key, MEAL_IMAGES["default"])

            # Render HTML Card
            st.markdown(f"""
                <div class="food-card">
                    <div class="food-img-container">
                        <img src="{final_image_url}" class="food-img" alt="{meal_type}">
                        <span class="meal-badge">{meal_type}</span>
                    </div>
                    <div class="food-details">
                        <div class="food-title">{dish_name}</div>
                        <div class="food-desc">{data.get('desc', '')}</div>
                        <div class="food-meta">
                            <span>🔥 {data.get('calories', 'N/A')}</span>
                            <span>🌿 Veg</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # The Button (Styled by CSS to attach to bottom of card)
            if st.button(f"🔄 Swap {meal_type}", key=f"swap_{meal_key}", use_container_width=True):
                regenerate_single_meal(meal_key, current_menu)

    render_card_with_action(c1, "Breakfast", current_menu.get('breakfast', {}))
    render_card_with_action(c2, "Lunch", current_menu.get('lunch', {}))
    render_card_with_action(c3, "Dinner", current_menu.get('dinner', {}))

    # --- INGREDIENTS & FOOTER ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    if current_menu.get('message'):
        st.success(f"**Chef's Note:** {current_menu['message']}")

    if current_menu.get('ingredients'):
        st.markdown(f"""
        <div class="ingredients-container">
            <div class="ing-header">🛒 Ingredients for Today</div>
            <div>
                {''.join([f'<span class="pill">{item}</span>' for item in current_menu['ingredients']])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Action Buttons Side-by-Side
    ac1, ac2 = st.columns(2, gap="medium")
    with ac1:
        if st.button("📲 Share Menu as Audio", use_container_width=True):
            with st.spinner("Generating audio..."):
                audio_file = text_to_speech(current_menu)
                if audio_file: st.audio(audio_file, format='audio/mp3', start_time=0)
    with ac2:
        if st.button("🔄 Shuffle Whole Menu", use_container_width=True):
            menu_data = generate_menu_ai()
            if menu_data:
                st.session_state.meal_plans[selected_date_str] = menu_data
                st.cache_data.clear()
                st.rerun()
