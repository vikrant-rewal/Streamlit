import streamlit as st
import requests
import datetime
import json
import os
import time
import random
from gtts import gTTS
import tempfile

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

# Reliable, high-quality static images (FALLBACK)
MEAL_IMAGES = {
    "breakfast": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    "lunch": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    "dinner": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    "default": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
}

LOADING_MESSAGES = [
    "🥕 Chopping the freshest vegetables...",
    "🍅 Simmering the sauces to perfection...",
    "🥬 Picking the best leaves from the garden...",
    "👨‍🍳 Claude is brainstorming your delicious day...",
    "🥑 Did you know? Healthy fats fuel your brain!",
    "🍋 Squeezing some zest into your life..."
]

# --- 3. CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    .stApp { background-color: #FFF9F5; font-family: 'Poppins', sans-serif; }
    h1, h2, h3 { color: #2D3436; font-weight: 600; }
    
    .main-header { text-align: center; padding: 20px 0; margin-bottom: 20px; }
    .main-header h1 { color: #FF6B6B; font-size: 2.5rem; margin: 0; }
    
    .food-card { 
        background: white; border-radius: 20px; overflow: hidden; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 25px; border: none;
        transition: transform 0.2s;
    }
    .food-card:hover { transform: translateY(-3px); }
    
    .food-img-container { height: 200px; overflow: hidden; position: relative; background: #f0f0f0; }
    .food-img { width: 100%; height: 100%; object-fit: cover; }
    .meal-badge { 
        position: absolute; top: 15px; left: 15px; background-color: #FF6B6B; color: white; 
        padding: 5px 15px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; 
    }
    
    .food-details { padding: 20px; }
    .food-title { font-size: 1.2rem; font-weight: 600; color: #2D3436; margin-bottom: 8px; }
    .food-desc { font-size: 0.9rem; color: #636E72; line-height: 1.5; }
    .food-meta { margin-top: 15px; padding-top: 15px; border-top: 1px dashed #eee; font-size: 0.8em; color: #B2BEC3; display: flex; justify-content: space-between; }

    .ingredients-box { background-color: #fff; border: 2px dashed #FF6B6B; border-radius: 15px; padding: 20px; margin-top: 20px; }
    .ing-title { color: #FF6B6B; font-weight: 600; font-size: 1.1em; margin-bottom: 10px; }

    .chef-loading { text-align: center; padding: 40px; background: white; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin: 20px 0; }
    .chef-loading-text { color: #FF6B6B; font-size: 1.2rem; font-weight: 600; margin-top: 15px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

    div.stButton > button { border-radius: 12px; font-weight: 600; border: none; }
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #FF6B6B 0%, #EE5253 100%); box-shadow: 0 4px 15px rgba(238, 82, 83, 0.4); }
    .stTextInput input { border-radius: 30px; padding-left: 20px; border: 1px solid #eee; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
    
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

# ==========================================
# --- 5. API FUNCTIONS (TEXT & IMAGE) ---
# ==========================================

# A. CLAUDE TEXT API (Haiku 3.5)
def call_claude_api(prompt_text):
    try:
        api_key = st.secrets["CLAUDE_API_KEY"]
    except:
        st.error("Missing CLAUDE_API_KEY in secrets.")
        return None

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt_text}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            st.error(f"Claude Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# B. GEMINI IMAGE API (gemini-2.0-flash-exp)
def call_gemini_image_api(prompt_text):
    try:
        # IMPORTANT: Get the separate Gemini Image Key from secrets
        api_key = st.secrets["GEMINI_IMAGE_KEY"]
    except:
        # Fail silently so fallback can take over, but log to console
        print("Missing GEMINI_IMAGE_KEY in secrets.")
        return None

    # Using the specific experimental model endpoint
    model = "gemini-2.0-flash-exp-image-generation"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    # Standard payload structure for Google Image models
    payload = {
        "instances": [
            {
                "prompt": prompt_text,
                 # 4:3 aspect ratio fits cards better
                "parameters": {"aspectRatio": "4:3"}
            }
        ]
    }

    try:
        # 30 second timeout for image generation
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            # Extract base64 data. Structure varies, checking common locations.
            if 'predictions' in result and result['predictions']:
                 prediction = result['predictions'][0]
                 # Check for standard base64 field
                 if 'bytesBase64Encoded' in prediction:
                     return prediction['bytesBase64Encoded']
                 # Check for alternative format
                 elif 'image' in prediction and 'b64' in prediction['image']:
                     return prediction['image']['b64']
        # If status isn't 200 or structure is wrong, return None to trigger fallback
        return None
    except Exception:
        return None

# C. CACHED IMAGE WRAPPER (Handles caching and data URI formatting)
@st.cache_data(show_spinner=False, ttl=3600*24) # Cache for 24 hours
def get_food_image(dish_name):
    if not dish_name or dish_name == 'Food':
         return None

    clean_name = dish_name.split('+')[0].strip()
    # Detailed prompt for better results
    prompt = f"A delicious, professional food photography shot of the vegetarian Indian dish '{clean_name}', served in an authentic setting. Cinematic lighting, high resolution, appetizing."

    base64_data = call_gemini_image_api(prompt)

    if base64_data:
        # Success: Return formatted data URI
        return f"data:image/jpeg;base64,{base64_data}"
    else:
        # Failure: Return None to trigger static fallback
        return None

# ==========================================
# --- 6. STATE & DATE FIX ---
# ==========================================
if 'preferences' not in st.session_state: st.session_state.preferences = load_memory()
if 'meal_plans' not in st.session_state: st.session_state.meal_plans = {} 

# IST Fix
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
today_ist = datetime.datetime.now(IST).date()

if 'selected_date' not in st.session_state: st.session_state.selected_date = today_ist
if st.session_state.selected_date < today_ist: st.session_state.selected_date = today_ist

# Sidebar
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
for i in range(5):
    day_date = today_ist + datetime.timedelta(days=i)
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
    Constraints: Vegetarian. NO {dislikes}. NO South Indian.
    Variety: RECENTLY EATEN: {past_str}. DO NOT REPEAT THESE. Use variety (Mushrooms, Corn, Soy, Kathal, etc).
    
    TASK: Generate a menu AND a shopping list of main ingredients required for all 3 meals combined.
    
    Output STRICT JSON format only: {{ 
        "breakfast": {{ "dish": "", "desc": "", "calories": "" }}, 
        "lunch": {{ "dish": "", "desc": "", "calories": "" }}, 
        "dinner": {{ "dish": "", "desc": "", "calories": "" }}, 
        "message": "Chef's Tip",
        "ingredients": ["Item 1", "Item 2", "Item 3", "etc..."] 
    }}
    """
    
    loading_placeholder = st.empty()
    random_msg = random.choice(LOADING_MESSAGES)
    
    loading_placeholder.markdown(f"""
        <div class="chef-loading">
            <div style="font-size: 3rem;">🥘</div>
            <div class="chef-loading-text">{random_msg}</div>
        </div>
    """, unsafe_allow_html=True)
    
    text_resp = call_claude_api(prompt)
    loading_placeholder.empty()
    
    if text_resp:
        try: 
            start = text_resp.find('{')
            end = text_resp.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text_resp[start:end])
            else:
                return json.loads(text_resp)
        except: st.error("Chef's handwriting was messy. Try again.")
    return None

if not current_menu:
    st.info(f"No plan for {st.session_state.selected_date.strftime('%A')}. Let's make one!")
    if st.button("✨ Create Menu", type="primary", use_container_width=True):
        menu_data = generate_menu_ai()
        if menu_data:
            st.session_state.meal_plans[selected_date_str] = menu_data
            st.rerun()
else:
    # Render Cards with GEMINI AI IMAGES + FALLBACK
    def render_card(meal_type, data):
        dish_name = data.get('dish', 'Food')
        meal_key = meal_type.lower()
        
        # 1. Try to get AI Image (Cached)
        # We use a spinner here as it might take a moment the first time
        with st.spinner(f"Garnishing {meal_key}..."):
             ai_image_url = get_food_image(dish_name)

        # 2. Determine final image URL (AI or Fallback)
        if ai_image_url:
            final_image_url = ai_image_url
        else:
            # Fallback to static image if AI failed
            final_image_url = MEAL_IMAGES.get(meal_key, MEAL_IMAGES["default"])

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

    c1, c2, c3 = st.columns(3)
    with c1: render_card("Breakfast", current_menu.get('breakfast', {}))
    with c2: render_card("Lunch", current_menu.get('lunch', {}))
    with c3: render_card("Dinner", current_menu.get('dinner', {}))

    if "message" in current_menu:
        st.success(f"**Chef's Note:** {current_menu['message']}")

    # Ingredients
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
            with st.spinner("Generating audio..."):
                audio_file = text_to_speech(current_menu)
                if audio_file:
                    st.audio(audio_file, format='audio/mp3', start_time=0)
    with c_btn2:
        if st.button("🔄 Shuffle Menu", use_container_width=True):
            menu_data = generate_menu_ai()
            if menu_data:
                st.session_state.meal_plans[selected_date_str] = menu_data
                # Clear image cache so new dishes get new images
                st.cache_data.clear()
                st.rerun()

    # --- INPUT SECTION ---
    st.markdown("---")
    
    with st.container():
        with st.form(key='custom_request', clear_on_submit=True):
            col_in, col_btn = st.columns([5, 1], gap="small")
            with col_in:
                text_req = st.text_input("Request", 
                                       placeholder="✨ E.g. Swap lunch for a salad, or make dinner spicy...", 
                                       label_visibility="collapsed")
            with col_btn:
                submitted = st.form_submit_button("➤", type="primary", use_container_width=True)

    if submitted and text_req:
        with st.spinner("Adjusting menu..."):
            curr = json.dumps(current_menu)
            # STRICT Prompt to ensure valid JSON return even for partial updates
            p = f"""
            You are a JSON-only API. 
            Current Menu JSON: {curr}
            User Request: "{text_req}"
            
            Task:
            1. Parse the User Request.
            2. If they dislike a specific dish or ingredient (e.g., 'no kathal'), REPLACE that specific meal (Breakfast, Lunch, or Dinner) with a new, different vegetarian Indian option.
            3. Update the 'ingredients' list to reflect the changes.
            4. Keep the other meals unchanged unless requested.
            5. RETURN ONLY THE VALID JSON. Do not write any introduction or explanation.
            """
            
            text_response = call_claude_api(p)
            
            if text_response:
                try:
                    start = text_response.find('{')
                    end = text_response.rfind('}') + 1
                    clean_json = text_response[start:end]
                    new_data = json.loads(clean_json)
                    st.session_state.meal_plans[selected_date_str] = new_data
                    # Clear image cache on update too
                    st.cache_data.clear()
                    st.rerun()
                except: st.error("Could not understand the update.")
