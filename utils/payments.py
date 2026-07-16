"""
Payment Module for EduGenius (Global Edition)
Handles Lemon Squeezy payments
"""

import streamlit as st
import requests
import urllib.parse

def get_ls_config():
    """Get Lemon Squeezy configuration"""
    return {
        'api_key': st.secrets.get("LEMON_SQUEEZY_API_KEY", ""),
        'store_id': st.secrets.get("LEMON_SQUEEZY_STORE_ID", ""),
    }

def get_supabase_client():
    from supabase import create_client
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

def verify_subscription(email: str = None):
    """Verify user's subscription status"""
    config = get_ls_config()
    
    if not email:
        return False, None, "No email provided"
    
    try:
        response = requests.get(
            f"https://api.lemonsqueezy.com/v1/subscriptions?filter[user_email]={email}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {config['api_key']}"
            }
        )
        
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            for sub in data['data']:
                status = sub['attributes']['status']
                if status in ['active', 'on_trial']:
                    product_name = sub['attributes']['product_name']
                    plan = 'pro' if 'Pro' in product_name else 'school'
                    return True, plan, f"Active {plan} subscription"
        
        return False, None, "No active subscription found"
        
    except Exception as e:
        return False, None, f"Verification error: {str(e)}"

def upgrade_user_in_db(firebase_uid: str, plan: str):
    """Update user subscription tier in Supabase"""
    supabase = get_supabase_client()
    
    try:
        supabase.table("users").update({
            "subscription_tier": plan,
            "subscription_status": "active"
        }).eq("firebase_uid", firebase_uid).execute()
        return True
    except:
        return False

def get_pricing_plans():
    """Return pricing plan information"""
    return {
        'free': {
            'name': 'Free',
            'price': '$0',
            'period': 'forever',
            'description': 'For individual teachers testing the workflow',
            'features': [
                '5 worksheets per month',
                'IGCSE & IB curricula',
                'Basic question types',
                'Lab calculator tools'
            ],
            'not_included': [
                'PDF export',
                'Marking schemes',
                'Worksheet history',
                'Custom templates'
            ]
        },
        'pro': {
            'name': 'Pro',
            'price': '$9.99',
            'period': 'per month',
            'description': 'For individual teachers who need speed and repeatability',
            'popular': True,
            'variant_id': st.secrets.get("LS_PRO_VARIANT_ID", ""),
            'features': [
                '♾️ Unlimited worksheets',
                'All question types',
                'PDF & document export',
                'Detailed marking schemes',
                'Worksheet history',
                'Custom templates',
                'Priority AI generation',
                'Full lab assistant suite',
                'Email support'
            ]
        },
        'school': {
            'name': 'School',
            'price': '$49.99',
            'period': 'per month',
            'description': 'For departments and schools standardizing resources',
            'variant_id': st.secrets.get("LS_SCHOOL_VARIANT_ID", ""),
            'features': [
                'Everything in Pro',
                '5 teacher accounts',
                'Shared worksheet bank',
                'Department collaboration',
                'Admin dashboard',
                'Bulk generation',
                'Custom branding',
                'Training session',
                'Priority support'
            ]
        }
    }

def render_payment_button(plan: str, user_data: dict):
    """Render payment button for Lemon Squeezy checkout"""
    
    if plan == 'free' or not user_data:
        return
    
    firebase_uid = user_data.get('localId', '')
    user_email = user_data.get('email', '')
    user_name = st.session_state.get('user_name', 'Teacher')
    
    plans = get_pricing_plans()
    plan_info = plans.get(plan, {})
    variant_id = plan_info.get('variant_id', '')
    store_id = st.secrets.get("LEMON_SQUEEZY_STORE_ID", "")
    
    if not variant_id or not store_id:
        st.error("Payment system is being set up. Please check back soon.")
        return
    
    # Build checkout URL with custom data
    params = urllib.parse.urlencode({
        'checkout[email]': user_email,
        'checkout[name]': user_name,
        'checkout[custom][firebase_uid]': firebase_uid,
        'checkout[custom][plan]': plan
    })
    
    checkout_url = f"https://store.lemonsqueezy.com/checkout?cart[variant_id]={variant_id}&{params}"
    
    st.markdown(f"""
    <a href="{checkout_url}" target="_blank" style="text-decoration:none;">
        <button style="
            width:100%;
            padding:14px;
            background:linear-gradient(135deg, #FF6B35, #F7931E);
            color:white;
            border:none;
            border-radius:12px;
            font-size:16px;
            font-weight:600;
            cursor:pointer;
        ">
            💳 Pay with Card / M-Pesa Global
        </button>
    </a>
    """, unsafe_allow_html=True)
    
    st.caption("🔒 Secure checkout by Lemon Squeezy • Visa, Mastercard, M-Pesa Global, Google Pay, Apple Pay")
    
    st.markdown("---")
    
    # Verify payment section
    st.markdown("**Already paid?**")
    verify_email = st.text_input(
        "Email used for payment",
        value=user_email,
        key=f"verify_{plan}"
    )
    
    if st.button("✅ Verify Payment & Activate", use_container_width=True, key=f"activate_{plan}"):
        with st.spinner("Checking your subscription..."):
            success, tier, message = verify_subscription(email=verify_email)
            if success:
                # Upgrade in our database
                upgrade_user_in_db(firebase_uid, tier)
                st.success(f"🎉 Your {tier.title()} plan is now active!")
                st.balloons()
                st.session_state.user_data = None
                st.rerun()
            else:
                st.warning(message or "No subscription found. Complete payment first, then verify.")
    
    st.info("💡 Complete payment on Lemon Squeezy, then return here and click **Verify Payment** to activate your account.")