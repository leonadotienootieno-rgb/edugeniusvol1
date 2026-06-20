"""
EduGenius v1.0
AI-Powered Worksheet Generator for International Curricula
Supports: Cambridge IGCSE, IB, KCSE (Sciences & Mathematics)
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# Import utilities
from utils.groq_client import generate_worksheet, generate_quick_quiz
from utils.pdf_generator import generate_download_button

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="EduGenius - AI Worksheet Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# LOAD CSS
# ============================================
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================
# SESSION STATE
# ============================================
def init_session():
    defaults = {
        'user_email': None,
        'subscription': 'free',  # free, pro, school
        'worksheets_generated': 0,
        'current_worksheet': None,
        'lab_logbook': [],
        'page': 'worksheet',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ============================================
# CONSTANTS
# ============================================
MAX_FREE_WORKSHEETS = 3
APP_NAME = "EduGenius"
APP_VERSION = "1.0.0"

# ============================================
# LOAD SYLLABUS DATA
# ============================================
@st.cache_data
def load_syllabus(curriculum):
    """Load syllabus data from JSON files"""
    syllabus_files = {
        "Cambridge IGCSE": "igcse_syllabus.json",
        "International Baccalaureate (IB)": "ib_syllabus.json",
    }
    
    filename = syllabus_files.get(curriculum)
    if not filename:
        return None
    
    filepath = Path(__file__).parent / "data" / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None

# ============================================
# SIDEBAR
# ============================================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"# 📚 {APP_NAME}")
        st.caption(f"AI Worksheet Generator v{APP_VERSION}")
        
        st.markdown("---")
        
        # User section
        if st.session_state.user_email:
            st.success(f"👤 {st.session_state.user_email}")
            st.caption(f"Plan: {st.session_state.subscription.title()}")
        else:
            with st.expander("🔐 Sign In (Free)"):
                email = st.text_input("Email", placeholder="teacher@school.edu")
                if st.button("Get Started", use_container_width=True):
                    if "@" in email:
                        st.session_state.user_email = email
                        st.session_state.worksheets_generated = 0
                        st.rerun()
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        
        if st.button("📝 Worksheet Generator", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.rerun()
        
        if st.button("📋 My Worksheets", use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()
        
        if st.button("🧪 Lab Assistant", use_container_width=True):
            st.session_state.page = 'lab'
            st.rerun()
        
        if st.button("💎 Pricing", use_container_width=True):
            st.session_state.page = 'pricing'
            st.rerun()
        
        st.markdown("---")
        
        # Usage
        if st.session_state.subscription == 'free':
            remaining = max(0, MAX_FREE_WORKSHEETS - st.session_state.worksheets_generated)
            st.metric("Free Worksheets Left", remaining)
            if remaining == 0:
                st.warning("Limit reached! Upgrade to Pro.")
                if st.button("⭐ Upgrade Now", use_container_width=True, type="primary"):
                    st.session_state.page = 'pricing'
                    st.rerun()
        
        st.markdown("---")
        st.caption("© 2024 EduGenius | All rights reserved")

# ============================================
# WORKSHEET GENERATOR PAGE
# ============================================
def page_worksheet_generator():
    st.markdown('<h1 class="main-header">📝 AI Worksheet Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Create exam-quality worksheets in seconds — not hours</p>', unsafe_allow_html=True)
    
    # Check usage limit
    if st.session_state.subscription == 'free' and st.session_state.worksheets_generated >= MAX_FREE_WORKSHEETS:
        st.error(f"⚠️ You've used all {MAX_FREE_WORKSHEETS} free worksheets this session.")
        st.markdown("### Upgrade to Pro for Unlimited Worksheets")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Free", f"{MAX_FREE_WORKSHEETS}/session")
        with col2:
            st.metric("Pro", "Unlimited ♾️")
        
        if st.button("✨ Upgrade to Pro - $9.99/month", use_container_width=True, type="primary"):
            st.session_state.page = 'pricing'
            st.rerun()
        return
    
    # Worksheet configuration form
    with st.form("worksheet_form"):
        st.markdown("### 1. Select Curriculum & Subject")
        
        col1, col2 = st.columns(2)
        with col1:
            curriculum = st.selectbox(
                "Curriculum",
                ["Cambridge IGCSE", "International Baccalaureate (IB)"],
                help="Choose the exam board"
            )
        with col2:
            syllabus = load_syllabus(curriculum)
            if syllabus:
                subjects = list(syllabus["subjects"].keys())
                subject = st.selectbox("Subject", subjects)
            else:
                st.error("Syllabus data not found")
                subject = None
        
        st.markdown("### 2. Choose Topic & Settings")
        
        if syllabus and subject:
            topic_data = syllabus["subjects"][subject]["topics"]
            
            col1, col2 = st.columns(2)
            with col1:
                # Get the level (Form equivalent)
                level = st.selectbox("Level", list(topic_data.keys()))
            
            if level:
                topics = list(topic_data[level].keys())
                with col2:
                    topic = st.selectbox("Topic", topics)
                
                if topic:
                    subtopics = topic_data[level][topic]
                    selected_subtopics = st.multiselect(
                        "Subtopics (select all that apply, or leave empty for whole topic)",
                        subtopics,
                        default=subtopics[:min(3, len(subtopics))]
                    )
        
        st.markdown("### 3. Question Settings")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            question_type = st.selectbox(
                "Question Type",
                ["Mixed", "Multiple Choice", "Structured Questions", "Essay Questions", "Practical/Data Analysis"]
            )
        with col2:
            num_questions = st.slider("Number of Questions", 5, 30, 10, 5)
        with col3:
            difficulty = st.selectbox(
                "Difficulty Level",
                ["Mixed", "Easy", "Medium", "Hard", "Exam Style"]
            )
        
        include_ms = st.checkbox("Include Marking Scheme / Answer Key", value=True)
        
        st.markdown("---")
        
        submitted = st.form_submit_button("🚀 Generate Worksheet", use_container_width=True, type="primary")
    
    # Handle generation
    if submitted:
        if not st.session_state.user_email:
            st.warning("Please sign in first (sidebar)")
            return
        
        with st.spinner("🤖 AI is creating your worksheet..."):
            st.info(f"Generating {num_questions} {difficulty.lower()} {question_type.lower()} questions on {topic}...")
            
            worksheet = generate_worksheet(
                curriculum=curriculum,
                subject=subject,
                topic=topic,
                subtopics=selected_subtopics if 'selected_subtopics' in locals() else [],
                question_type=question_type,
                num_questions=num_questions,
                difficulty=difficulty,
                include_marking_scheme=include_ms
            )
            
            if worksheet:
                st.session_state.current_worksheet = {
                    'text': worksheet,
                    'subject': subject,
                    'topic': topic,
                    'curriculum': curriculum,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'settings': {
                        'question_type': question_type,
                        'num_questions': num_questions,
                        'difficulty': difficulty
                    }
                }
                
                st.session_state.worksheets_generated += 1
                
                st.success("✅ Worksheet generated successfully!")
                st.rerun()
            else:
                st.error("Failed to generate worksheet. Please check your API key and try again.")
    
    # Display current worksheet
    if st.session_state.current_worksheet:
        st.markdown("---")
        st.markdown("### 📄 Your Generated Worksheet")
        
        ws = st.session_state.current_worksheet
        
        # Worksheet metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"Curriculum: {ws['curriculum']}")
        with col2:
            st.caption(f"Subject: {ws['subject']}")
        with col3:
            st.caption(f"Generated: {ws['date']}")
        
        # Display worksheet
        with st.container():
            st.markdown(f"""
            <div class="worksheet-output">
                {ws['text'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
        
        # Actions
        col1, col2, col3 = st.columns(3)
        with col1:
            generate_download_button(
                ws['text'],
                ws['subject'],
                ws['topic'],
                ws['curriculum']
            )
        with col2:
            if st.button("📝 Generate Another", use_container_width=True):
                st.session_state.current_worksheet = None
                st.rerun()
        with col3:
            # Copy to clipboard
            st.button("📋 Copy Text", use_container_width=True)
            st.code(ws['text'], language=None)

# ============================================
# LAB ASSISTANT PAGE
# ============================================
def page_lab_assistant():
    st.markdown('<h1 class="main-header">🧪 Lab Assistant</h1>', unsafe_allow_html=True)
    st.caption("Free scientific calculators — included with EduGenius")
    
    calculators = [
        ("🧬 Dilution (C1V1)", "Calculate solution preparation volumes"),
        ("🧫 Microbiology", "Doubling time & growth curves"),
        ("🔬 Cell Culture", "Cell seeding calculator"),
        ("🧬 DNA Normalization", "PCR and sequencing setup"),
        ("🧪 Master Mix", "PCR master mix recipe generator"),
        ("🔄 Unit Converter", "Molarity, percentage solutions"),
        ("🌀 Centrifuge", "RPM to RCF converter"),
        ("⏱️ Lab Timer", "Experiment countdown timer"),
    ]
    
    selected = st.selectbox(
        "Choose a calculator",
        [f"{emoji} {name}" for emoji, name in calculators]
    )
    
    # Simple dilution calculator as demo
    if "Dilution" in selected:
        st.markdown("### 🧬 Solution Dilution Calculator")
        st.markdown("*C₁V₁ = C₂V₂*")
        
        col1, col2 = st.columns(2)
        with col1:
            c1 = st.number_input("Stock Conc. (M)", 1.0, format="%.4f")
            c2 = st.number_input("Target Conc. (M)", 0.1, format="%.4f")
        with col2:
            v2 = st.number_input("Target Vol. (mL)", 100.0)
        
        if st.button("Calculate", use_container_width=True):
            if c1 > 0:
                v1 = (c2 * v2) / c1
                st.success(f"Add **{v1:.2f} mL** stock + **{v2-v1:.2f} mL** diluent")
    
    else:
        st.info("👆 Select a calculator above. More calculators coming soon!")
    
    st.markdown("---")
    st.markdown("### 💡 Need more lab tools?")
    st.markdown("Pro users get advanced calculators, protocol templates, and lab inventory management.")
    
    if st.button("Explore Pro Features", use_container_width=True):
        st.session_state.page = 'pricing'
        st.rerun()

# ============================================
# PRICING PAGE
# ============================================
def page_pricing():
    st.markdown('<h1 class="main-header">💎 Choose Your Plan</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Start free. Upgrade when you need more.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <h3>🆓 Free</h3>
            <h1 style="font-size:3rem;">$0</h1>
            <p>Forever</p>
            <hr>
            <p>✅ 3 worksheets/month</p>
            <p>✅ Basic question types</p>
            <p>✅ IGCSE & IB subjects</p>
            <p>✅ Lab calculators</p>
            <p>✅ Online access</p>
            <p>❌ PDF export</p>
            <p>❌ Marking schemes</p>
            <p>❌ Worksheet history</p>
            <p>❌ Custom templates</p>
            <br>
            <p style="color:#666; font-size:0.9rem;">Great for trying out</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Free", use_container_width=True):
            st.session_state.subscription = 'free'
            st.session_state.page = 'worksheet'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="pricing-card featured">
            <div style="background:#FF6B35; color:white; padding:4px 12px; border-radius:20px; 
                        display:inline-block; margin-bottom:12px; font-size:0.8rem;">
                MOST POPULAR
            </div>
            <h3>💎 Pro</h3>
            <h1 style="font-size:3rem; color:#FF6B35;">$9.99</h1>
            <p>per month</p>
            <hr>
            <p>✅ ♾️ Unlimited worksheets</p>
            <p>✅ All question types</p>
            <p>✅ PDF & Word export</p>
            <p>✅ Detailed marking schemes</p>
            <p>✅ Worksheet history</p>
            <p>✅ Custom templates</p>
            <p>✅ Priority AI generation</p>
            <p>✅ Lab assistant (full)</p>
            <p>✅ Email support</p>
            <br>
            <p style="color:#FF6B35; font-weight:600;">Best for individual teachers</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Go Pro", use_container_width=True, type="primary"):
            st.session_state.subscription = 'pro'
            st.balloons()
            st.success("🎉 Payment integration coming soon! Email pro@edugenius.app")
    
    with col3:
        st.markdown("""
        <div class="pricing-card">
            <h3>🏫 School</h3>
            <h1 style="font-size:3rem;">$49.99</h1>
            <p>per month</p>
            <hr>
            <p>✅ Everything in Pro</p>
            <p>✅ 5 teacher accounts</p>
            <p>✅ Shared worksheet bank</p>
            <p>✅ Department collaboration</p>
            <p>✅ Admin dashboard</p>
            <p>✅ Bulk generation</p>
            <p>✅ Custom branding</p>
            <p>✅ Priority support</p>
            <p>✅ Training session</p>
            <br>
            <p style="color:#666; font-size:0.9rem;">For departments & schools</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Contact Sales", use_container_width=True):
            st.info("📧 Email: schools@edugenius.app")
    
    st.markdown("---")
    st.markdown("### 💡 Why teachers love EduGenius")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="text-align:center; padding:20px;">
            <h2>⏱️</h2>
            <h4>Save 3+ Hours</h4>
            <p>Per worksheet. Generate in seconds what used to take all evening.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:20px;">
            <h2>🎯</h2>
            <h4>Exam-Aligned</h4>
            <p>Questions match IGCSE, IB, and KCSE exam formats and difficulty.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="text-align:center; padding:20px;">
            <h2>📊</h2>
            <h4>Auto-Graded</h4>
            <p>Marking schemes included. Save hours of grading preparation.</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# MAIN APP
# ============================================
def main():
    render_sidebar()
    
    pages = {
        'worksheet': page_worksheet_generator,
        'lab': page_lab_assistant,
        'pricing': page_pricing,
        'history': lambda: st.info("📋 Worksheet history — coming soon! Upgrade to Pro to save your worksheets."),
    }
    
    current_page = st.session_state.get('page', 'worksheet')
    
    if current_page in pages:
        pages[current_page]()
    else:
        page_worksheet_generator()

if __name__ == "__main__":
    main()