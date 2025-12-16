import streamlit as st
import google.generativeai as genai
import datetime
import json
import os

# --- PAGE CONFIGURATION (Must be first) ---
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

# --- 2. CSS STYLING (The "Mobile App" Look) ---
st.markdown("""
    <style>
    /* Clean background and text */
    .stApp {
        background-color: #F8F9FA;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Calendar Strip Styling */
    .calendar-strip {
        display: flex;
        justify-content: space-between;
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .date-card {
        text-align: center;
        padding: 5px 10px;
        border-radius: 10px;
        cursor: pointer;
    }
    .date-card.active {
        background-color: #6C63FF;
        color: white;
        font-weight: bold;
    }
    .date-card .day { font-size: 0.8em; color: #888; }
    .date-card.active .day { color: #eee; }
    
    /* Food Card Styling */
    .food-card {
        background: white;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .food-card:hover {
        transform: translateY(-2px);
    }
    .food-img-container {
        height: 180px;
        overflow: hidden;
        background-color: #eee;
    }
    .food-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .food-details {
        padding: 15px;
    }
    .food-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }
    .food-desc {
        font-size: 0.9em;
        color: #666;
    }
    .meal-badge {
        background-color: #E8E8FF;
        color: #6C63FF;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.7em;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    /* Hide Streamlit default elements for cleaner look */
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
    # Uses Pollinations.ai for simple AI generated images or keyword search placeholders
    # Cleaning the name for better search
    clean_name = dish_name.split('+')[0].strip().replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/delicious%20indian%20food%20{clean_name}%20high%20quality%20photography?width=400&height=300&nologo=true"

# --- 4. APP LOGIC ---

# Initialize Session State
if 'preferences' not in st.session_state:
    st.session_state.preferences = load_memory()
if 'generated_menu' not in st.session_state:
    st.session_state.generated_menu = None
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# Configure Gemini
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.warning("⚠️ API Key missing in Secrets.")
except Exception as e:
    st.error(f"API Error: {e}")

# Sidebar for "Memory" control
with st.sidebar:
    st.header("🧠 Chef's Memory")
    st.write("I remember you hate:")
    
    # Display dislikes as tags
    dislikes_str = ", ".join(st.session_state.preferences["dislikes"])
    st.info(dislikes_str)
    
    new_dislike = st.text_input("Add a new dislike:")
    if st.button("Remember this"):
        if new_dislike and new_dislike not in st.session_state.preferences["dislikes"]:
            st.session_state.preferences["dislikes"].append(new_dislike)
            save_memory(st.session_state.preferences)
            st.rerun()

    st.markdown("---")
    st.write("Also avoiding: South Indian visuals (Dosa/Idli) requiring fermentation equipment.")

# --- 5. MAIN UI ---

# Header
st.markdown("### 🥗 Mumbai Family Meal Planner")

# Calendar Strip (Visual Only)
cols = st.columns(5)
today = datetime.date.today()
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

for i, col in enumerate(cols):
    day_date = today + datetime.timedelta(days=i)
    is_selected = (day_date == st.session_state.selected_date)
    
    # Visual logic for the calendar
    style_class = "date-card active" if is_selected else "date-card"
    
    with col:
        st.markdown(f"""
            <div class="{style_class}">
                <div class="day">{days[day_date.weekday()]}</div>
                <div class="date">{day_date.day}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Generation Logic
def generate_menu_ai():
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    dislikes = ", ".join(st.session_state.preferences["dislikes"])
    is_weekend = st.session_state.selected_date.weekday() >= 5
    
    prompt = f"""
    You are a smart family cook for 3 vegetarians in Mumbai. 
    
    STRICT CONSTRAINTS:
    1. Diet: Vegetarian. NO Meat, NO Eggs.
    2. AVOID ingredients: {dislikes}.
    3. AVOID complex South Indian dishes (Idli, Dosa, Appam) that need grinders/fermentation.
    4. STYLE: Home-cooked North Indian/Mumbai style. 
    
    CONTEXT:
    - Today is: {st.session_state.selected_date.strftime("%A")}
    - Weekend Mode: {"YES (Remind to check headcount)" if is_weekend else "NO"}
    
    TASK:
    Generate a menu JSON for Breakfast, Lunch, and Dinner.
    
    OUTPUT FORMAT (Strict JSON):
    {{
        "breakfast": {{ "dish": "Name", "desc": "Short appetizing description", "calories": "approx kcal" }},
        "lunch": {{ "dish": "Name", "desc": "Short appetizing description", "calories": "approx kcal" }},
        "dinner": {{ "dish": "Name", "desc": "Short appetizing description", "calories": "approx kcal" }},
        "message": "Any note about ingredients or headcount"
    }}
    """
    
    with st.spinner("👨‍🍳 Chef is thinking..."):
        try:
            response = model.generate_content(prompt)
            # Clean up JSON string if Gemini adds markdown markers
            clean_json = response.text.replace("```json", "").replace("```", "")
            return json.loads(clean_json)
        except Exception as e:
            st.error(f"Chef got confused: {e}")
            return None

# Generate Button
if st.button("✨ Plan My Day", type="primary", use_container_width=True):
    menu_data = generate_menu_ai()
    if menu_data:
        st.session_state.generated_menu = menu_data

# Display Cards
if st.session_state.generated_menu:
    menu = st.session_state.generated_menu
    
    # Helper to render card
    def render_card(meal_type, data):
        image_url = get_food_image_url(data['dish'])
        st.markdown(f"""
        <div class="food-card">
            <div class="food-img-container">
                <img src="{image_url}" class="food-img" alt="{data['dish']}">
            </div>
            <div class="food-details">
                <span class="meal-badge">{meal_type}</span>
                <div class="food-title">{data['dish']}</div>
                <div class="food-desc">{data['desc']}</div>
                <div style="margin-top: 10px; font-size: 0.8em; color: #888;">
                    🔥 {data.get('calories', 'N/A')} • 🌿 Veg
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render the 3 meals
    render_card("Breakfast", menu['breakfast'])
    render_card("Lunch", menu['lunch'])
    render_card("Dinner", menu['dinner'])
    
    if "message" in menu and menu["message"]:
        st.info(f"💡 Note: {menu['message']}")

# Voice/Chat Input for corrections
st.markdown("### 🗣️ Talk to the Chef")
feedback = st.chat_input("Ex: 'I don't want Pasta, give me something Indian'")

if feedback:
    if not st.session_state.generated_menu:
        st.warning("Generate a menu first!")
    else:
        # Re-roll logic
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Current Menu: {json.dumps(st.session_state.generated_menu)}
        User Feedback: "{feedback}"
        Constraints: Keep dislikes in mind ({", ".join(st.session_state.preferences["dislikes"])}).
        Task: Update the menu JSON based on feedback. Keep unchanged items same.
        OUTPUT: JSON only.
        """
        with st.spinner("Adjusting menu..."):
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "")
            st.session_state.generated_menu = json.loads(clean_json)
            st.rerun()
