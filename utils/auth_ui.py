"""
Authentication UI Components for EduGenius
"""

import streamlit as st
from utils.auth import sign_up, sign_in, sign_out, is_authenticated, get_user_tier

def render_auth_sidebar():
    """Render authentication section in sidebar"""
    
    with st.sidebar:
        if is_authenticated():
            _render_authenticated_user()
        else:
            _render_login_form()

def _render_login_form():
    """Render login/signup form"""
    st.markdown("### 🔐 Account")
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        with st.form("signin_form"):
            email = st.text_input("Email", key="signin_email", placeholder="teacher@school.edu")
            password = st.text_input("Password", type="password", key="signin_password")
            
            if st.form_submit_button("Sign In", use_container_width=True):
                if not email or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Signing in..."):
                        user, error = sign_in(email, password)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.firebase_user = user
                            st.success("✅ Welcome back!")
                            st.rerun()
    
    with tab2:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name", key="signup_name", placeholder="Mr. John Smith")
            email = st.text_input("Email", key="signup_email", placeholder="teacher@school.edu")
            password = st.text_input("Password", type="password", key="signup_password", help="At least 6 characters")
            
            if st.form_submit_button("Create Free Account", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please fill in all required fields")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating your account..."):
                        user, error = sign_up(email, password, full_name)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.firebase_user = user
                            st.success("🎉 Account created! You have 5 free worksheets.")
                            st.balloons()
                            st.rerun()

def _render_authenticated_user():
    """Render UI for logged-in users"""
    user = st.session_state.firebase_user
    user_data = get_user_tier()
    tier = user_data.get('subscription_tier', 'free')
    
    st.markdown("### 👤 Account")
    
    tier_badges = {'free': '🟢 Free', 'pro': '💎 Pro', 'school': '🏫 School'}
    st.markdown(f"**{tier_badges.get(tier, '🟢 Free')} Plan**")
    
    if tier == 'free':
        used = user_data.get('worksheets_generated', 0)
        limit = st.secrets.get("MAX_FREE_WORKSHEETS", 5)
        st.progress(used / limit, text=f"📊 {used}/{limit} worksheets used")
    
    st.markdown("---")
    
    if st.button("📝 New Worksheet", use_container_width=True):
        st.session_state.page = 'worksheet'
        st.rerun()
    
    if st.button("📋 My History", use_container_width=True):
        st.session_state.page = 'history'
        st.rerun()
    
    if st.button("🧪 Lab Tools", use_container_width=True):
        st.session_state.page = 'lab'
        st.rerun()
    
    if tier == 'free':
        st.markdown("---")
        if st.button("⭐ Upgrade to Pro", use_container_width=True, type="primary"):
            st.session_state.page = 'pricing'
            st.rerun()
    
    st.markdown("---")
    if st.button("🚪 Sign Out", use_container_width=True):
        sign_out()
        st.rerun()