import streamlit as st
import requests
import datetime
import json
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Mumbai Meal Planner",
    page_icon="🍛",
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
    
    /* Calendar Strip */
    .calendar-strip { display: flex; justify-content: space-between; background: white; padding: 15px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .date-card { text-align: center; padding: 5px 10px; border-radius: 10px; cursor: pointer; }
    .date-card.active { background-color: #FF4B4B; color: white; font-weight: bold; }
    .date-card .day { font-size: 0.8em; color: #888; }
    .date-card.active .day { color: #eee; }
    
    /* Food Card */
    .food-card { background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .food-img-container { height: 180px; overflow: hidden; background-color: #eee; }
    .food-img { width: 100%; height: 100%; object-fit: cover; }
    .food-details { padding: 15px; }
    .food-title { font-size: 1.2em; font-weight: bold; color: #333; margin-bottom: 5px; }
    .food-desc { font-size: 0.9em; color: #666; }
    .meal-badge { background-color: #FFE5E5; color: #FF4B4B; padding: 4px 10px; border-radius: 12px; font-size: 0.7em; font-weight: bold; text-transform: uppercase; display: inline-block; margin-bottom: 8px; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_PREFERENCES

def save_memory(prefs):
    with open(MEMORY_FILE, "w") as f:
        json.dump(prefs, f)

def get_food_image_url(dish_name):
    clean_name = dish_name.split('+')[0].strip().replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/delicious%20indian%20food%20{clean_name}%20high%20quality%20photography?width=400&height=300&nologo=true"

# --- 4. THE DIRECT API CALL (Updated for Gemini 2.5) ---
def call_gemini_direct(prompt_text):
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # UPDATED MODEL URL: Using gemini-2.5-flash from your list
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
            
        data = response.json()
        
        # Check if 'candidates' exists in response
        if "candidates" not in data or not data["candidates"]:
            st.error(f"No candidates returned. Full response: {data}")
            return None
            
        return data["candidates"][0]["content"]["parts"][0]["text"]
        
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- 5. APP LOGIC ---
if 'preferences' not in st.session_state:
    st.session_state.preferences = load_memory()
if 'generated_menu' not in st.session_state:
    st.session_state.generated_menu = None
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

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

# --- 6. MAIN UI ---
st.markdown("### 🥗 Mumbai Family Meal Planner")

# Calendar Strip
cols = st.columns(5)
today = datetime.date.today()
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
for i, col in enumerate(cols):
    day_date = today + datetime.timedelta(days=i)
    is_selected = (day_date == st.session_state.selected_date)
    style_class = "date-card active" if is_selected else "date-card"
    with col:
        st.markdown(f"""
            <div class="{style_class}">
                <div class="day">{days[day_date.weekday()]}</div>
                <div class="date">{day_date.day}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

def generate_menu_ai():
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    is_weekend = st.session_state.selected_date.weekday() >= 5
    
    prompt = f"""
    You are a smart family cook for 3 vegetarians in Mumbai. 
    STRICT CONSTRAINTS:
    1. Diet: Vegetarian. NO Meat, NO Eggs.
    2. AVOID ingredients: {dislikes}.
    3. NO South Indian (Idli, Dosa, Appam).
    4. STYLE: Home-cooked North Indian/Mumbai style. 
    
    CONTEXT:
    - Today is: {st.session_state.selected_date.strftime("%A")}
    - Weekend Mode: {"YES (Remind to check headcount)" if is_weekend else "NO"}
    
    TASK:
    Generate a JSON for Breakfast, Lunch, Dinner.
    
    OUTPUT JSON FORMAT:
    {{
        "breakfast": {{ "dish": "Name", "desc": "Short description", "calories": "kcal" }},
        "lunch": {{ "dish": "Name", "desc": "Short description", "calories": "kcal" }},
        "dinner": {{ "dish": "Name", "desc": "Short description", "calories": "kcal" }},
        "message": "Note about ingredients"
    }}
    """
    
    with st.spinner("👨‍🍳 Chef is thinking..."):
        text_response = call_gemini_direct(prompt)
        if text_response:
            try:
                # Clean up json markdown if present
                clean_json = text_response.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except json.JSONDecodeError:
                st.error("Chef's handwriting was messy (JSON Error). Try again.")
                # Optional: Show raw text for debugging
                # st.write(text_response)
                return None
        return None

if st.button("✨ Plan My Day", type="primary", use_container_width=True):
    menu_data = generate_menu_ai()
    if menu_data:
        st.session_state.generated_menu = menu_data

if st.session_state.generated_menu:
    menu = st.session_state.generated_menu
    
    def render_card(meal_type, data):
        dish_name = data.get('dish', 'Food')
        image_url = get_food_image_url(dish_name)
        
        st.markdown(f"""
        <div class="food-card">
            <div class="food-img-container"><img src="{image_url}" class="food-img"></div>
            <div class="food-details">
                <span class="meal-badge">{meal_type}</span>
                <div class="food-title">{dish_name}</div>
                <div class="food-desc">{data.get('desc', '')}</div>
                <div style="margin-top: 10px; font-size: 0.8em; color: #888;">🔥 {data.get('calories', 'N/A')} • 🌿 Veg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_card("Breakfast", menu.get('breakfast', {}))
    render_card("Lunch", menu.get('lunch', {}))
    render_card("Dinner", menu.get('dinner', {}))
    
    if "message" in menu:
        st.info(f"💡 {menu['message']}")

st.markdown("### 🗣️ Talk to the Chef")
feedback = st.chat_input("Ex: 'I don't want Pasta, give me something Indian'")
if feedback and st.session_state.generated_menu:
    with st.spinner("Adjusting menu..."):
        prompt = f"Update menu based on feedback: {feedback}. Previous Menu: {json.dumps(st.session_state.generated_menu)}. Output JSON only."
        text_response = call_gemini_direct(prompt)
        if text_response:
            try:
                clean_json = text_response.replace("```json", "").replace("```", "").strip()
                st.session_state.generated_menu = json.loads(clean_json)
                st.rerun()
            except:
                st.error("Could not understand the update.")
