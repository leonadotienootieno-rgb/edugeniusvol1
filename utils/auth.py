"""
Authentication Module for EduGenius
Handles Firebase Auth + Supabase User Management
"""

import streamlit as st
import pyrebase
from supabase import create_client

def get_firebase_config():
    """Get Firebase config from secrets"""
    return {
        "apiKey": st.secrets["FIREBASE_API_KEY"],
        "authDomain": st.secrets["FIREBASE_AUTH_DOMAIN"],
        "projectId": st.secrets["FIREBASE_PROJECT_ID"],
        "storageBucket": st.secrets["FIREBASE_STORAGE_BUCKET"],
        "messagingSenderId": st.secrets["FIREBASE_MESSAGING_SENDER_ID"],
        "appId": st.secrets["FIREBASE_APP_ID"]
    }

def get_supabase_client():
    """Get authenticated Supabase client"""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

def init_firebase():
    """Initialize Firebase"""
    try:
        firebase = pyrebase.initialize_app(get_firebase_config())
        return firebase.auth()
    except Exception as e:
        st.error(f"Firebase init error: {e}")
        return None

def sign_up(email: str, password: str, full_name: str = ""):
    """Create new user account"""
    auth = init_firebase()
    if not auth:
        return None, "Authentication service unavailable"
    
    try:
        user = auth.create_user_with_email_and_password(email, password)

        st.session_state["local_profile"] = {
            "email": email,
            "full_name": full_name,
            "subscription_tier": "free",
            "worksheets_generated": 0
        }
        st.session_state["local_worksheets"] = []

        try:
            supabase = get_supabase_client()
            supabase.table("users").insert({
                "email": email,
                "firebase_uid": user['localId'],
                "full_name": full_name,
                "subscription_tier": "free",
                "worksheets_generated": 0
            }).execute()
        except Exception:
            # Keep account creation working even when the database profile insert is temporarily unavailable.
            pass
        
        return user, None
    except Exception as e:
        error_msg = str(e)
        if "EMAIL_EXISTS" in error_msg:
            return None, "This email is already registered. Please sign in."
        elif "WEAK_PASSWORD" in error_msg:
            return None, "Password should be at least 6 characters."
        return None, f"Sign up failed. Please try again."

def sign_in(email: str, password: str):
    """Sign in existing user"""
    auth = init_firebase()
    if not auth:
        return None, "Authentication service unavailable"
    
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user, None
    except Exception as e:
        error_msg = str(e)
        if "INVALID_PASSWORD" in error_msg or "INVALID_LOGIN_CREDENTIALS" in error_msg:
            return None, "Incorrect email or password."
        elif "EMAIL_NOT_FOUND" in error_msg:
            return None, "No account found with this email."
        return None, "Sign in failed. Please try again."

def is_authenticated():
    """Check if user is logged in"""
    return 'firebase_user' in st.session_state

def get_user_tier():
    """Get current user's subscription tier"""
    if not is_authenticated():
        return {'subscription_tier': 'free', 'worksheets_generated': 0}

    local_profile = st.session_state.get('local_profile')
    if local_profile:
        return local_profile
    
    supabase = get_supabase_client()
    user = st.session_state.get('firebase_user')
    
    try:
        result = supabase.table("users")\
            .select("subscription_tier, worksheets_generated")\
            .eq("firebase_uid", user['localId'])\
            .execute()
        
        if result.data:
            return result.data[0]
        return {'subscription_tier': 'free', 'worksheets_generated': 0}
    except:
        return {'subscription_tier': 'free', 'worksheets_generated': 0}

def can_generate_worksheet():
    """Check if user can generate a worksheet"""
    user_data = get_user_tier()
    tier = user_data.get('subscription_tier', 'free')
    
    if tier in ['pro', 'school']:
        return True
    
    max_worksheets = st.secrets.get("MAX_FREE_WORKSHEETS", 5)
    return user_data.get('worksheets_generated', 0) < max_worksheets

def increment_worksheet_count():
    """Increment user's worksheet generation count"""
    if not is_authenticated():
        return

    local_profile = st.session_state.get('local_profile')
    if local_profile:
        local_profile['worksheets_generated'] = local_profile.get('worksheets_generated', 0) + 1
        return
    
    supabase = get_supabase_client()
    user = st.session_state.firebase_user
    
    current = get_user_tier()
    new_count = current.get('worksheets_generated', 0) + 1
    
    supabase.table("users")\
        .update({"worksheets_generated": new_count})\
        .eq("firebase_uid", user['localId'])\
        .execute()

def save_worksheet(curriculum, subject, topic, content, question_type="", difficulty=""):
    """Save generated worksheet to database"""
    if not is_authenticated():
        return False

    local_worksheets = st.session_state.setdefault('local_worksheets', [])
    if st.session_state.get('local_profile'):
        local_worksheets.append({
            "curriculum": curriculum,
            "subject": subject,
            "topic": topic,
            "question_type": question_type,
            "difficulty": difficulty,
            "content": content,
            "created_at": str(__import__('datetime').datetime.now())
        })
        return True
    
    supabase = get_supabase_client()
    user = st.session_state.firebase_user
    
    try:
        user_result = supabase.table("users")\
            .select("id")\
            .eq("firebase_uid", user['localId'])\
            .execute()
        
        if user_result.data:
            supabase.table("worksheets").insert({
                "user_id": user_result.data[0]['id'],
                "curriculum": curriculum,
                "subject": subject,
                "topic": topic,
                "question_type": question_type,
                "difficulty": difficulty,
                "content": content
            }).execute()
            return True
    except:
        local_worksheets.append({
            "curriculum": curriculum,
            "subject": subject,
            "topic": topic,
            "question_type": question_type,
            "difficulty": difficulty,
            "content": content,
            "created_at": str(__import__('datetime').datetime.now())
        })
        return True

def get_user_worksheets(limit=20):
    """Get user's saved worksheets"""
    if not is_authenticated():
        return []

    local_worksheets = st.session_state.get('local_worksheets', [])
    if st.session_state.get('local_profile'):
        return local_worksheets[-limit:][::-1]
    
    supabase = get_supabase_client()
    user = st.session_state.firebase_user
    
    try:
        user_result = supabase.table("users")\
            .select("id")\
            .eq("firebase_uid", user['localId'])\
            .execute()
        
        if user_result.data:
            worksheets = supabase.table("worksheets")\
                .select("*")\
                .eq("user_id", user_result.data[0]['id'])\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return worksheets.data
    except:
        return local_worksheets[-limit:][::-1]
    
    return []

def sign_out():
    """Sign out current user"""
    st.session_state.pop('firebase_user', None)
    st.session_state.pop('user_data', None)
    st.session_state.pop('local_profile', None)
    st.session_state.pop('local_worksheets', None)