"""
EduGenius v2.0
AI-Powered Worksheet Generator for IGCSE & IB
With Real Authentication & Global Payments
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# Import modules
from utils.groq_client import generate_worksheet, generate_quick_quiz
from utils.pdf_generator import generate_download_button
from utils.auth_ui import render_auth_sidebar
from utils.auth import (
    is_authenticated, get_user_tier, can_generate_worksheet,
    increment_worksheet_count, save_worksheet, get_user_worksheets
)
from utils.payments import get_pricing_plans, render_payment_button, verify_subscription, upgrade_user_in_db

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="EduGenius - AI Worksheet Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
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
        'page': 'worksheet',
        'current_worksheet': None,
        'active_template_mode': 'Worksheet',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ============================================
# LOAD SYLLABUS DATA
# ============================================
@st.cache_data
def load_syllabus(curriculum):
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
# PAGE: WORKSHEET GENERATOR
# ============================================
def page_worksheet():
    st.markdown('<h1 class="main-header">📝 AI Worksheet Generator</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="feature-banner">
        <div class="feature-banner-title">Build exam-ready teaching assets in under a minute</div>
        <div class="feature-banner-copy">Create curriculum-aligned worksheets, marking schemes, revision packs, and classroom-ready resources from one teacher-first workflow.</div>
        <div class="feature-banner-tags">
            <span>IGCSE</span>
            <span>IB</span>
            <span>Essay</span>
            <span>Practical</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚡ Teacher shortcuts")
    shortcut_col1, shortcut_col2, shortcut_col3 = st.columns(3)
    with shortcut_col1:
        if st.button("📘 Worksheet", use_container_width=True):
            st.session_state.active_template_mode = "Worksheet"
            st.rerun()
    with shortcut_col2:
        if st.button("🧠 Quick Quiz", use_container_width=True):
            st.session_state.active_template_mode = "Quick Quiz"
            st.rerun()
    with shortcut_col3:
        if st.button("📝 Revision Pack", use_container_width=True):
            st.session_state.active_template_mode = "Revision Pack"
            st.rerun()
    
    if not is_authenticated():
        st.info("👆 **Sign in from the sidebar** to start generating worksheets. It's free!")
        st.markdown("---")
        st.markdown("### Why teachers love EduGenius")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🎯 **Exam-aligned**\nIGCSE & IB format")
        with col2:
            st.markdown("⚡ **Save hours**\nGenerate in seconds")
        with col3:
            st.markdown("🆓 **5 free worksheets**\nNo credit card needed")
        return
    
    if not can_generate_worksheet():
        st.error("⚠️ You've used all your free worksheets this month.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🆓 Free Plan\n- 5 worksheets/month\n- Basic features")
        with col2:
            st.markdown("### 💎 Pro Plan\n- Unlimited worksheets\n- PDF export\n- $9.99/month")
        
        if st.button("✨ Upgrade to Pro", use_container_width=True, type="primary"):
            st.session_state.page = 'pricing'
            st.rerun()
        return
    
    with st.form("worksheet_form"):
        st.markdown("### 1. Choose Your Template")
        template_options = ["Worksheet", "Quick Quiz", "Revision Pack"]
        template_mode = st.selectbox(
            "Template Mode",
            template_options,
            help="Pick the classroom output you want to generate.",
            index=template_options.index(st.session_state.get('active_template_mode', 'Worksheet'))
        )
        st.session_state.active_template_mode = template_mode

        st.markdown("### 2. Curriculum & Subject")
        col1, col2 = st.columns(2)
        with col1:
            curriculum = st.selectbox("Curriculum", ["Cambridge IGCSE", "International Baccalaureate (IB)"])
        with col2:
            syllabus = load_syllabus(curriculum)
            subjects = list(syllabus["subjects"].keys()) if syllabus else []
            subject = st.selectbox("Subject", subjects)
        
        if syllabus and subject:
            st.markdown("### 3. Topic")
            topic_data = syllabus["subjects"][subject]["topics"]
            level = st.selectbox("Level", list(topic_data.keys()))
            
            if level:
                topic = st.selectbox("Topic", list(topic_data[level].keys()))
                if topic:
                    subtopics = topic_data[level][topic]
                    selected_subtopics = st.multiselect(
                        "Subtopics (leave all for whole topic)",
                        subtopics,
                        default=subtopics[:min(2, len(subtopics))]
                    )
        
        st.markdown("### 4. Settings")
        col1, col2, col3 = st.columns(3)
        with col1:
            if template_mode == "Quick Quiz":
                question_type = "Multiple Choice"
            else:
                question_type = st.selectbox("Type", ["Mixed", "Multiple Choice", "Structured", "Essay", "Practical"])
        with col2:
            num_questions = st.slider("Questions", 3 if template_mode == "Quick Quiz" else 5, 30, 5 if template_mode == "Quick Quiz" else 10, 1 if template_mode == "Quick Quiz" else 5)
        with col3:
            difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard", "Exam Style"])
        
        include_ms = st.checkbox("Include Marking Scheme", value=template_mode != "Quick Quiz")
        
        submitted = st.form_submit_button("🚀 Generate Learning Asset", use_container_width=True, type="primary")
    
    if submitted:
        with st.spinner("🤖 AI is creating your learning asset..."):
            if template_mode == "Quick Quiz":
                worksheet = generate_quick_quiz(
                    curriculum=curriculum,
                    subject=subject,
                    topic=topic,
                    num_questions=num_questions
                )
                loading_label = "Quick Quiz ready!"
            else:
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
                loading_label = "Worksheet ready!"
            
            if worksheet:
                st.session_state.current_worksheet = {
                    'text': worksheet,
                    'subject': subject,
                    'topic': topic,
                    'curriculum': curriculum,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'template_mode': template_mode,
                    'settings': {'question_type': question_type, 'num_questions': num_questions, 'difficulty': difficulty}
                }
                
                increment_worksheet_count()
                save_worksheet(curriculum, subject, topic, worksheet, question_type, difficulty)
                
                st.success(f"✅ {loading_label}")
                st.rerun()
            else:
                st.error("Failed to generate. Please check your connection and try again.")
    
    if st.session_state.current_worksheet:
        st.markdown("---")
        st.markdown("### 📄 Your Worksheet")
        
        ws = st.session_state.current_worksheet
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.caption(f"📚 {ws['curriculum']}")
        with col2: st.caption(f"📖 {ws['subject']} - {ws['topic']}")
        with col3: st.caption(f"🧩 {ws.get('template_mode', 'Worksheet')}")
        with col4: st.caption(f"🕐 {ws['date']}")
        
        st.text_area("", ws['text'], height=400, key="worksheet_display")
        
        col1, col2 = st.columns(2)
        with col1:
            generate_download_button(ws['text'], ws['subject'], ws['topic'], ws['curriculum'])
        with col2:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.current_worksheet = None
                st.rerun()

        if ws.get('template_mode'):
            st.info(f"💡 Fast reuse: your last asset was a {ws['template_mode']} for {ws['subject']} / {ws['topic']}. Pick a shortcut above to continue building from that workflow.")

# ============================================
# PAGE: PRICING
# ============================================
def page_pricing():
    st.markdown('<h1 class="main-header">💎 Choose Your Plan</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Start with 5 free worksheets. Upgrade when you need more power, export, and automation.</p>', unsafe_allow_html=True)

    plans = get_pricing_plans()
    user = st.session_state.get('firebase_user')

    st.markdown("""
    <div class="pricing-hero">
        <div><strong>Fast setup</strong></div>
        <div>Trusted by teachers, schools, and departments looking for an AI worksheet workflow that feels premium.</div>
    </div>
    """, unsafe_allow_html=True)

    school_col, value_col = st.columns([1.3, 0.7])
    with school_col:
        st.markdown("### 🏫 School & Department Pack")
        st.markdown("Use EduGenius to standardize worksheet creation across departments, save prep time, and centralize classroom resource quality.")
        st.markdown("- Shared worksheet bank")
        st.markdown("- Department-wide collaboration")
        st.markdown("- Admin and billing visibility")
        st.markdown("- Teacher seat management")
    with value_col:
        st.markdown("<div class='school-highlight'>Best for schools, departments, and curriculum leaders.</div>", unsafe_allow_html=True)

    st.markdown("---")
    trust_col1, trust_col2, trust_col3 = st.columns(3)
    with trust_col1:
        st.metric("Time saved", "8+ hrs/week")
    with trust_col2:
        st.metric("Teacher seats", "5 included")
    with trust_col3:
        st.metric("Value focus", "Consistency")

    st.markdown("---")
    st.markdown("### Why schools upgrade")
    st.markdown("- Standardize worksheets across a department")
    st.markdown("- Reduce repetitive prep time for every teacher")
    st.markdown("- Keep curriculum-aligned resources reusable and high quality")
    st.markdown("- Scale from one teacher to a whole school workflow")

    school_demo = st.container()
    with school_demo:
        st.markdown("<div class='school-cta'>School leaders can request rollout support, admin onboarding, and department-level adoption guidance.</div>", unsafe_allow_html=True)
        st.link_button("Request School Demo", "mailto:schools@edugenius.app?subject=EduGenius%20School%20Demo")

    st.markdown("---")
    st.markdown("### Choose the plan that fits your classroom")

    col1, col2, col3 = st.columns(3)

    for col, (plan_key, plan) in zip([col1, col2, col3], plans.items()):
        with col:
            is_popular = plan.get('popular', False)
            card_class = "pricing-card featured" if is_popular else "pricing-card"

            st.markdown(f"""
            <div class="{card_class}">
                <div class="pricing-badge">{'MOST POPULAR' if is_popular else plan['name'].upper()}</div>
                <h3>{plan['name']}</h3>
                <div class="pricing-price">{plan['price']}</div>
                <div class="pricing-period">{plan['period']}</div>
                <div style="color:#6b7280; margin-bottom:16px;">{plan.get('description', '')}</div>
                <hr>
                <div style="text-align:left;">
                    {''.join([f'<div class="pricing-feature">✅ {feature}</div>' for feature in plan.get('features', [])])}
                    {''.join([f'<div class="pricing-feature">❌ {feature}</div>' for feature in plan.get('not_included', [])])}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            if plan_key == 'free':
                if not is_authenticated():
                    if st.button("Get Started Free", use_container_width=True, key="free_start"):
                        st.session_state.page = 'worksheet'
                        st.rerun()
            else:
                if is_authenticated():
                    render_payment_button(plan_key, user)
                else:
                    if st.button(f"Sign Up for {plan['name']}", use_container_width=True, key=f"signup_{plan_key}"):
                        st.session_state.page = 'worksheet'
                        st.rerun()

# ============================================
# PAGE: HISTORY
# ============================================
def page_history():
    st.markdown('<h1 class="main-header">📋 Worksheet History</h1>', unsafe_allow_html=True)
    
    if not is_authenticated():
        st.info("Sign in to view your worksheet history.")
        return
    
    worksheets = get_user_worksheets()
    
    if not worksheets:
        st.info("No worksheets yet. Generate your first one!")
        if st.button("Create Worksheet", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.rerun()
        return
    
    recent_subjects = sorted({ws['subject'] for ws in worksheets})
    recent_topics = sorted({ws['topic'] for ws in worksheets})

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Saved resources", len(worksheets))
    with c2:
        st.metric("Curricula covered", len({ws['curriculum'] for ws in worksheets}))
    with c3:
        st.metric("Last activity", worksheets[0]['created_at'][:10])

    st.markdown("### Quick actions")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    with quick_col1:
        if st.button("Create another worksheet", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.rerun()
    with quick_col2:
        if st.button("Open pricing", use_container_width=True):
            st.session_state.page = 'pricing'
            st.rerun()
    with quick_col3:
        if st.button("Visit lab tools", use_container_width=True):
            st.session_state.page = 'lab'
            st.rerun()

    st.markdown("### Dashboard insights")
    insight_col1, insight_col2 = st.columns(2)
    with insight_col1:
        st.info(f"📚 Most-used subjects: {', '.join(recent_subjects[:3])}")
    with insight_col2:
        st.info(f"🧠 Recent topics: {', '.join(recent_topics[:3])}")

    st.markdown(f"### {len(worksheets)} Saved Worksheets")
    
    for ws in worksheets:
        with st.expander(f"📄 {ws['subject']} - {ws['topic']} ({ws['created_at'][:10]})"):
            st.caption(f"Curriculum: {ws['curriculum']} | Type: {ws['question_type']} | Difficulty: {ws['difficulty']}")
            st.text_area("", ws['content'], height=200, key=f"ws_{ws['id']}")
            
            generate_download_button(ws['content'], ws['subject'], ws['topic'], ws['curriculum'])

# ============================================
# PAGE: LAB ASSISTANT
# ============================================
def page_lab():
    st.markdown('<h1 class="main-header">🧪 Lab Assistant</h1>', unsafe_allow_html=True)
    st.caption("Free scientific calculators — included with EduGenius")
    
    st.markdown("### 🧬 Dilution Calculator (C₁V₁ = C₂V₂)")
    
    col1, col2 = st.columns(2)
    with col1:
        c1 = st.number_input("Stock Concentration (M)", 1.0, format="%.4f")
        c2 = st.number_input("Target Concentration (M)", 0.1, format="%.4f")
    with col2:
        v2 = st.number_input("Target Volume (mL)", 100.0)
    
    if st.button("Calculate", use_container_width=True):
        if c1 > 0:
            v1 = (c2 * v2) / c1
            st.success(f"✅ Add **{v1:.2f} mL** stock + **{v2-v1:.2f} mL** diluent")
    
    st.markdown("---")
    st.markdown("### 🔜 More lab tools coming for Pro users!")
    st.markdown("Centrifuge • Master Mix • Growth Curves • Protocol Templates")

# ============================================
# MAIN APP
# ============================================
def main():
    with st.sidebar:
        st.markdown("# 📚 EduGenius")
        st.caption("AI Worksheet Generator")
        st.markdown("---")
        
        render_auth_sidebar()
        
        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        
        if st.button("📝 Generator", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.rerun()
        if st.button("📋 History", use_container_width=True):
            st.session_state.page = 'history'
            st.rerun()
        if st.button("🧪 Lab Tools", use_container_width=True):
            st.session_state.page = 'lab'
            st.rerun()
        if st.button("💎 Pricing", use_container_width=True):
            st.session_state.page = 'pricing'
            st.rerun()
        
        st.markdown("---")
        st.caption("© 2024 EduGenius")
    
    pages = {
        'worksheet': page_worksheet,
        'history': page_history,
        'lab': page_lab,
        'pricing': page_pricing,
    }
    
    current_page = st.session_state.get('page', 'worksheet')
    if current_page in pages:
        pages[current_page]()

if __name__ == "__main__":
    main()