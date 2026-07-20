"""
EduGenius v2.0
AI-Powered Worksheet Generator for IGCSE & IB
With Real Authentication & Global Payments
"""

import streamlit as st
import json
import urllib.parse
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
        'school_rollout': None,
        'school_teacher_invites': [],
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

    st.markdown("""
    <div class="workflow-grid">
        <div class="workflow-card">
            <div class="workflow-step">1</div>
            <div class="workflow-title">Choose your curriculum</div>
            <div class="workflow-copy">Pick IGCSE or IB, then the subject and topic your lesson needs.</div>
        </div>
        <div class="workflow-card">
            <div class="workflow-step">2</div>
            <div class="workflow-title">Set the format</div>
            <div class="workflow-copy">Switch between worksheet, quick quiz, and revision pack in one click.</div>
        </div>
        <div class="workflow-card">
            <div class="workflow-step">3</div>
            <div class="workflow-title">Generate and export</div>
            <div class="workflow-copy">Create exam-ready teaching content and download it for classroom use.</div>
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
        st.markdown("""
        <div class="value-strip">
            <div class="value-strip-title">Create your teacher workspace in 30 seconds</div>
            <div class="value-strip-copy">Sign in from the sidebar, choose your curriculum, and generate classroom-ready assets without spending time building content from scratch.</div>
        </div>
        """, unsafe_allow_html=True)

        cta_col1, cta_col2 = st.columns(2)
        with cta_col1:
            if st.button("Start Free", use_container_width=True, type="primary"):
                st.session_state.page = 'worksheet'
                st.rerun()
        with cta_col2:
            if st.button("View Pricing", use_container_width=True):
                st.session_state.page = 'pricing'
                st.rerun()

        st.markdown("---")
        st.markdown("### Why teachers choose EduGenius")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='value-card'><div class='value-label'>🎯 Exam-aligned</div><div class='value-copy'>IGCSE & IB workflows built for classroom consistency.</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='value-card'><div class='value-label'>⚡ Save hours</div><div class='value-copy'>Go from topic to teaching resource in a single flow.</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='value-card'><div class='value-label'>🆓 Free to start</div><div class='value-copy'>5 worksheets monthly with no payment required.</div></div>", unsafe_allow_html=True)
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
# COMPONENT: PRICING CARD
# ============================================
def render_pricing_card(plan_key, plan, user_signed_in):
    """Render a single pricing card with a consistent premium action flow."""
    is_popular = plan.get('popular', False)
    card_class = "pricing-card featured" if is_popular else "pricing-card"

    feature_markup = ''.join([
        f'<div class="pricing-feature">✅ {feature}</div>'
        for feature in plan.get('features', [])
    ])
    excluded_markup = ''.join([
        f'<div class="pricing-feature muted">❌ {feature}</div>'
        for feature in plan.get('not_included', [])
    ])

    st.markdown(f"""
    <div class="{card_class}">
        <div class="pricing-badge">{'MOST POPULAR' if is_popular else plan['name'].upper()}</div>
        <h3>{plan['name']}</h3>
        <div class="pricing-price">{plan['price']}</div>
        <div class="pricing-period">{plan['period']}</div>
        <div class="pricing-description">{plan.get('description', '')}</div>
        <hr>
        <div class="pricing-list">{feature_markup}{excluded_markup}</div>
    </div>
    """, unsafe_allow_html=True)

    if plan_key == 'free':
        if not user_signed_in:
            if st.button("Get Started Free", use_container_width=True, key=f"free_start_{plan_key}"):
                st.session_state.page = 'worksheet'
                st.rerun()
    else:
        if user_signed_in:
            render_payment_button(plan_key, st.session_state.get('firebase_user'))
        else:
            if st.button(f"Sign Up for {plan['name']}", use_container_width=True, key=f"signup_{plan_key}"):
                st.session_state.page = 'worksheet'
                st.rerun()

    st.markdown("---")

# ============================================
# PAGE: PRICING
# ============================================
def page_pricing():
    st.markdown('<h1 class="main-header">💎 Choose Your Plan</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Start with 5 free worksheets. Upgrade when you need more power, export, and automation.</p>', unsafe_allow_html=True)

    plans = get_pricing_plans()

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

    st.markdown("""
    <div class="demo-card">
        <div class="demo-card-title">School rollout support</div>
        <div class="demo-card-copy">School leaders can request onboarding, department rollout guidance, admin setup, and a guided demo for multi-teacher adoption.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("school_demo_form"):
        st.markdown("### 🏫 Request a department demo")
        demo_col1, demo_col2 = st.columns(2)
        with demo_col1:
            school_name = st.text_input("School / Department", placeholder="Nairobi International School")
            contact_name = st.text_input("Your Name", placeholder="Head of Science")
        with demo_col2:
            email = st.text_input("Work Email", placeholder="admin@school.edu")
            teacher_seats = st.number_input("Estimated teacher seats", min_value=1, max_value=500, value=10)

        message = st.text_area(
            "What are you hoping to improve?",
            placeholder="We want standardized worksheets across our science department and faster prep for 30 teachers.",
            height=120
        )

        submitted = st.form_submit_button("Request School Demo", use_container_width=True, type="primary")

    if submitted:
        params = urllib.parse.urlencode({
            'subject': 'EduGenius School Demo Request',
            'body': (
                f"School / Department: {school_name}\n"
                f"Contact Name: {contact_name}\n"
                f"Work Email: {email}\n"
                f"Estimated Teacher Seats: {teacher_seats}\n\n"
                f"Need / Goal:\n{message}"
            )
        })
        demo_mailto = f"mailto:schools@edugenius.app?{params}"
        st.success("✅ Your demo request is ready. Use the link below to send it to the EduGenius team.")
        st.markdown(f"<a class='demo-link' href='{demo_mailto}'>📩 Open email draft</a>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🏫 School rollout workspace")
    rollout = st.session_state.get('school_rollout')

    if rollout:
        st.markdown("""
        <div class="rollout-panel">
            <div class="demo-card-title">Admin overview</div>
            <div class="demo-card-copy">Use this workspace to review the rollout shape, teacher seat plan, and department readiness before you commit to a broader launch.</div>
        </div>
        """, unsafe_allow_html=True)

        rollout_col1, rollout_col2, rollout_col3 = st.columns(3)
        with rollout_col1:
            st.metric("Department", rollout['department'])
        with rollout_col2:
            st.metric("Seats", rollout['seats'])
        with rollout_col3:
            st.metric("Phase", rollout['phase'])

        readiness_col1, readiness_col2 = st.columns(2)
        with readiness_col1:
            st.markdown("### Readiness checklist")
            st.checkbox("Curriculum mapping complete", value=True)
            st.checkbox("Teacher pilot cohort confirmed", value=True)
            st.checkbox("Department template standards selected", value=True)
        with readiness_col2:
            st.markdown("### Rollout milestones")
            st.markdown("1. Pilot group onboarding")
            st.markdown("2. Weekly content review")
            st.markdown("3. Department-wide launch")
            st.markdown(f"Assigned admin: **{rollout['owner']}**")

    with st.form("school_rollout_form"):
        rollout_col1, rollout_col2 = st.columns(2)
        with rollout_col1:
            rollout_department = st.text_input("Department name", placeholder="Science Department")
            rollout_seats = st.number_input("Seat allocation target", min_value=1, max_value=500, value=10)
        with rollout_col2:
            rollout_phase = st.selectbox("Rollout phase", ["Pilot", "Department rollout", "School-wide launch"])
            rollout_owner = st.text_input("Assigned admin", placeholder="Curriculum Lead")

        if st.form_submit_button("Save rollout plan", use_container_width=True, type="primary"):
            st.session_state.school_rollout = {
                'department': rollout_department or 'Science Department',
                'seats': rollout_seats,
                'phase': rollout_phase,
                'owner': rollout_owner or 'Curriculum Lead',
            }
            st.success("✅ School rollout plan saved for this session.")
            st.rerun()

    st.markdown("---")
    st.markdown("### 👥 Invite teacher cohort")
    invites = st.session_state.get('school_teacher_invites', [])

    summary_seats = st.session_state.get('school_rollout', {}).get('seats', 10) if st.session_state.get('school_rollout') else 10
    invite_count = len(invites)
    seat_utilization = min(invite_count / max(summary_seats, 1), 1.0)

    dashboard_col1, dashboard_col2, dashboard_col3 = st.columns(3)
    with dashboard_col1:
        st.metric("Invited teachers", invite_count)
    with dashboard_col2:
        st.metric("Seat target", summary_seats)
    with dashboard_col3:
        st.metric("Coverage", f"{round(seat_utilization * 100)}%")

    st.progress(seat_utilization, text="Teacher seat rollout status")

    with st.form("teacher_invite_form"):
        invite_col1, invite_col2 = st.columns(2)
        with invite_col1:
            invite_email = st.text_input("Teacher email", placeholder="teacher@school.edu")
        with invite_col2:
            invite_role = st.selectbox("Role", ["Teacher", "Department Lead", "Admin"])

        if st.form_submit_button("Add invite", use_container_width=True):
            if invite_email:
                invites.append({
                    'email': invite_email,
                    'role': invite_role,
                })
                st.session_state.school_teacher_invites = invites
                st.success("✅ Teacher invite added to the rollout workspace.")
                st.rerun()
            else:
                st.warning("Please enter a teacher email.")

    if invites:
        st.markdown("<div class='invite-list'>", unsafe_allow_html=True)
        for invite in invites:
            st.markdown(f"<div class='invite-pill'>{invite['email']} · {invite['role']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Choose the plan that fits your classroom")

    col1, col2, col3 = st.columns(3)
    user_signed_in = is_authenticated()

    for col, (plan_key, plan) in zip([col1, col2, col3], plans.items()):
        with col:
            render_pricing_card(plan_key, plan, user_signed_in)

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
        st.markdown("""
        <div class="history-empty-card">
            <div class="history-title">Your teaching workspace is ready</div>
            <div class="history-copy">Create your first worksheet and it will appear here with quick reuse actions and export options.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Create Worksheet", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.rerun()
        return
    
    recent_subjects = sorted({ws['subject'] for ws in worksheets})
    recent_topics = sorted({ws['topic'] for ws in worksheets})

    st.markdown("""
    <div class="history-hero">
        <div class="history-title">Your teaching workspace</div>
        <div class="history-copy">Review recent resources, reopen past topics, and keep your classroom prep flowing without starting from scratch.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Saved resources", len(worksheets))
    with c2:
        st.metric("Curricula covered", len({ws['curriculum'] for ws in worksheets}))
    with c3:
        st.metric("Last activity", worksheets[0]['created_at'][:10])

    template_counts = {
        'Worksheet': 0,
        'Quick Quiz': 0,
        'Revision Pack': 0
    }
    curriculum_counts = {}
    for ws in worksheets:
        template_mode = ws.get('template_mode', 'Worksheet')
        template_counts[template_mode] = template_counts.get(template_mode, 0) + 1
        curriculum = ws.get('curriculum', 'Unknown')
        curriculum_counts[curriculum] = curriculum_counts.get(curriculum, 0) + 1

    top_curriculum = max(curriculum_counts, key=curriculum_counts.get)

    st.markdown("### Teaching analytics")
    analytics_col1, analytics_col2, analytics_col3 = st.columns(3)
    with analytics_col1:
        st.metric("Worksheets", template_counts.get('Worksheet', 0))
    with analytics_col2:
        st.metric("Quick quizzes", template_counts.get('Quick Quiz', 0))
    with analytics_col3:
        st.metric("Revision packs", template_counts.get('Revision Pack', 0))

    st.markdown(f"<div class='analytics-strip'>Most active curriculum: <strong>{top_curriculum}</strong> with {curriculum_counts[top_curriculum]} resources</div>", unsafe_allow_html=True)

    st.markdown("### Reuse your most recent workflow")
    recent_subject = worksheets[0]['subject']
    recent_topic = worksheets[0]['topic']
    recent_curriculum = worksheets[0]['curriculum']
    reuse_col1, reuse_col2, reuse_col3 = st.columns(3)
    with reuse_col1:
        if st.button("📘 Continue with last topic", use_container_width=True, type="primary"):
            st.session_state.page = 'worksheet'
            st.session_state.active_template_mode = 'Worksheet'
            st.rerun()
    with reuse_col2:
        if st.button("🧠 Create quick quiz", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.session_state.active_template_mode = 'Quick Quiz'
            st.rerun()
    with reuse_col3:
        if st.button("📝 Build revision pack", use_container_width=True):
            st.session_state.page = 'worksheet'
            st.session_state.active_template_mode = 'Revision Pack'
            st.rerun()

    st.markdown(f"<div class='reuse-strip'>Recent teaching pattern: {recent_curriculum} · {recent_subject} · {recent_topic}</div>", unsafe_allow_html=True)

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

    if st.session_state.get('current_worksheet'):
        last_ws = st.session_state.current_worksheet
        st.markdown("### Continue from your most recent draft")
        st.markdown(f"• {last_ws['curriculum']} · {last_ws['subject']} · {last_ws['topic']} ({last_ws['template_mode']})")
        if st.button("Resume last draft", use_container_width=True, type="primary"):
            st.session_state.page = 'worksheet'
            st.rerun()

    st.markdown(f"### {len(worksheets)} Saved Worksheets")
    
    for ws in worksheets:
        with st.expander(f"📄 {ws['subject']} - {ws['topic']} ({ws['created_at'][:10]})"):
            st.caption(f"Curriculum: {ws['curriculum']} | Type: {ws['question_type']} | Difficulty: {ws['difficulty']}")
            st.text_area("", ws['content'], height=200, key=f"ws_{ws['id']}")
            
            generate_download_button(ws['content'], ws['subject'], ws['topic'], ws['curriculum'])

# ============================================
# PAGE: SCHOOL ADMIN DASHBOARD

def page_school_admin():
    st.markdown('<h1 class="main-header">🏫 School Admin Dashboard</h1>', unsafe_allow_html=True)

    if not is_authenticated():
        st.info("Sign in to access the school admin workspace and rollout analytics.")
        return

    worksheets = get_user_worksheets()
    invites = st.session_state.get('school_teacher_invites', [])
    rollout = st.session_state.get('school_rollout') or {}
    seat_target = rollout.get('seats', 10)
    invite_count = len(invites)
    template_counts = {'Worksheet': 0, 'Quick Quiz': 0, 'Revision Pack': 0}
    curriculum_counts = {}

    for ws in worksheets:
        mode = ws.get('template_mode', 'Worksheet')
        template_counts[mode] = template_counts.get(mode, 0) + 1
        curriculum = ws.get('curriculum', 'Unknown')
        curriculum_counts[curriculum] = curriculum_counts.get(curriculum, 0) + 1

    top_curriculum = max(curriculum_counts, key=curriculum_counts.get) if curriculum_counts else 'None yet'
    progress_value = min(invite_count / max(seat_target, 1), 1.0)

    st.markdown("""
    <div class="admin-dashboard">
        <div class="admin-dashboard-title">Manage your school rollout and teacher adoption from one place.</div>
        <div class="admin-dashboard-copy">Track invite progress, worksheet adoption, and curriculum focus. This dashboard is designed for department leads and school admins.</div>
    </div>
    """, unsafe_allow_html=True)

    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("Invited teachers", invite_count)
    with summary_col2:
        st.metric("Seat target", seat_target)
    with summary_col3:
        st.metric("Worksheets created", len(worksheets))

    st.markdown(f"<div class='analytics-strip'>Most active curriculum: <strong>{top_curriculum}</strong></div>", unsafe_allow_html=True)
    st.progress(progress_value, text="Teacher invite coverage")

    st.markdown("### Rollout status")
    phase = rollout.get('phase', 'Not configured')
    owner = rollout.get('owner', 'Not assigned')
    department = rollout.get('department', 'Not configured')

    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.metric("Department", department)
    with status_col2:
        st.metric("Phase", phase)
    with status_col3:
        st.metric("Owner", owner)

    if invites:
        st.markdown("### Invited cohort")
        st.markdown("<div class='invite-list'>", unsafe_allow_html=True)
        for invite in invites:
            st.markdown(f"<div class='invite-pill'>{invite['email']} · {invite['role']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### School analytics")
    analytics_col1, analytics_col2 = st.columns(2)
    with analytics_col1:
        st.info(f"📊 Templates used: Worksheets {template_counts['Worksheet']}, Quizzes {template_counts['Quick Quiz']}, Revision {template_counts['Revision Pack']}")
    with analytics_col2:
        st.info(f"📚 Curricula active: {', '.join([f'{k} ({v})' for k,v in curriculum_counts.items()][:3])}")

    if st.button("Open worksheet history", use_container_width=True):
        st.session_state.page = 'history'
        st.rerun()

    if st.button("Visit pricing & plans", use_container_width=True):
        st.session_state.page = 'pricing'
        st.rerun()

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
        if st.button("🏫 School Admin", use_container_width=True):
            st.session_state.page = 'school_admin'
            st.rerun()
        
        st.markdown("---")
        st.caption("© 2024 EduGenius")
    
    pages = {
        'worksheet': page_worksheet,
        'history': page_history,
        'lab': page_lab,
        'pricing': page_pricing,
        'school_admin': page_school_admin,
    }
    
    current_page = st.session_state.get('page', 'worksheet')
    if current_page in pages:
        pages[current_page]()

if __name__ == "__main__":
    main()