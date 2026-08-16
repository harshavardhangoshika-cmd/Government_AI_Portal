import streamlit as st
import base64
import os
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "app", "frontend", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

SRC_VIKSIT = r"C:\Users\harsh\.gemini\antigravity-ide\brain\26d28044-2344-40be-8055-fb4996b29081\media__1786906536025.jpg"
DST_VIKSIT = os.path.join(ASSETS_DIR, "viksit_bharat.jpg")

if os.path.exists(SRC_VIKSIT) and not os.path.exists(DST_VIKSIT):
    try:
        shutil.copy(SRC_VIKSIT, DST_VIKSIT)
    except Exception:
        pass


def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            mime = "image/png" if image_path.endswith(".png") else "image/jpeg"
            return f"data:{mime};base64,{encoded}"
    return ""


SKYLINE_B64 = get_base64_image(DST_VIKSIT) if os.path.exists(DST_VIKSIT) else get_base64_image(SRC_VIKSIT)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Government AI Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None


# ============================================================
# DEMO USERS
# ============================================================

USERS = {
    "official@gov.in": {
        "password": "official123",
        "role": "Government Official"
    },
    "citizen@gov.in": {
        "password": "citizen123",
        "role": "Citizen"
    }
}


# ============================================================
# CUSTOM STYLING (DARK THEME)
# ============================================================

st.markdown(
    '<style>'
    '.stApp { background-color: #0b0f17; color: #f8fafc; }'
    'div.stButton > button[kind="primary"] { background-color: #e63946 !important; border-color: #e63946 !important; color: white !important; font-weight: 700 !important; border-radius: 8px !important; height: 48px !important; transition: all 0.3s ease !important; }'
    'div.stButton > button[kind="primary"]:hover { background-color: #d62828 !important; border-color: #d62828 !important; box-shadow: 0 4px 14px rgba(230, 57, 70, 0.4) !important; }'
    'div.stButton > button[kind="secondary"] { background-color: #1e293b !important; border: 1px solid #334155 !important; color: #cbd5e1 !important; font-weight: 600 !important; border-radius: 8px !important; transition: all 0.3s ease !important; }'
    'div.stButton > button[kind="secondary"]:hover { background-color: #334155 !important; border-color: #e63946 !important; color: #ffffff !important; }'
    '.stTextInput input { background-color: #1e293b !important; color: #ffffff !important; border: 1px solid #334155 !important; border-radius: 8px !important; }'
    '.stTextInput input:focus { border-color: #e63946 !important; box-shadow: 0 0 0 1px #e63946 !important; }'
    'header {visibility: hidden;}'
    'footer {visibility: hidden;}'
    '</style>',
    unsafe_allow_html=True
)


# ============================================================
# LOGIN PAGE LANDING VIEW
# ============================================================

def login_page():

    # --------------------------------------------------------
    # 1. TOP HEADER / NAVBAR
    # --------------------------------------------------------

    st.markdown(
        '<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0px 20px 0px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 30px;">'
        '<div style="display: flex; align-items: center; gap: 15px;">'
        '<div style="font-size: 32px;">🏛️</div>'
        '<div>'
        '<div style="font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; font-family: system-ui, sans-serif;">Government AI Portal</div>'
        '<div style="display: flex; gap: 4px; height: 3px; width: 140px; margin-top: 4px;">'
        '<div style="background: #f97316; flex: 1; border-radius: 2px;"></div>'
        '<div style="background: #ffffff; flex: 1; border-radius: 2px;"></div>'
        '<div style="background: #22c55e; flex: 1; border-radius: 2px;"></div>'
        '</div>'
        '</div>'
        '</div>'
        '<div style="background: rgba(255,255,255,0.06); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); color: #e2e8f0; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px;">'
        '<span>[A]</span>'
        '<span>English</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # 2. HERO SECTION + SPIDER-MAN POSTER / LOGIN CARD
    # --------------------------------------------------------

    hero_col1, hero_col2 = st.columns([1.1, 0.9], gap="large")

    with hero_col1:
        st.markdown(
            '<div style="padding-right: 15px;">'
            '<div style="color: #e63946; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px;">Welcome to</div>'
            '<h1 style="font-size: 52px; font-weight: 900; color: #ffffff; margin: 0px 0px 12px 0px; line-height: 1.05; letter-spacing: -1px; font-family: system-ui, sans-serif;">Government<br><span style="color: #ffffff;">AI Portal</span></h1>'
            '<div style="width: 45px; height: 3px; background: #e63946; margin-bottom: 22px; border-radius: 2px;"></div>'
            '<h3 style="font-size: 20px; font-weight: 700; color: #f1f5f9; margin-bottom: 12px; line-height: 1.3;">Empowering Citizens.<br>Enabling Smarter Governance.</h3>'
            '<p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin-bottom: 25px; max-width: 480px;">AI-Powered platform for complaint management, analytics, and data-driven decision making.</p>'
            '</div>',
            unsafe_allow_html=True
        )


    with hero_col2:

        # ----------------------------------------------------
        # SPIDER-MAN POSTER ARTWORK
        # ----------------------------------------------------

        st.markdown(
            '<div style="background: radial-gradient(circle at center, #8b0000 0%, #3a0000 65%, #0f0505 100%); border-radius: 20px; padding: 35px 25px; text-align: center; border: 1px solid rgba(230, 57, 70, 0.4); box-shadow: 0 12px 35px rgba(230, 57, 70, 0.25); position: relative; overflow: hidden; margin-bottom: 25px;">'
            '<svg style="position: absolute; top:0; left:0; width:100%; height:100%; opacity: 0.22; pointer-events:none;" viewBox="0 0 500 500">'
            '<circle cx="250" cy="250" r="50" fill="none" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<circle cx="250" cy="250" r="110" fill="none" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<circle cx="250" cy="250" r="170" fill="none" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<circle cx="250" cy="250" r="230" fill="none" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<line x1="0" y1="250" x2="500" y2="250" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<line x1="250" y1="0" x2="250" y2="500" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<line x1="75" y1="75" x2="425" y2="425" stroke="#ff4d4d" stroke-width="2.5"/>'
            '<line x1="425" y1="75" x2="75" y2="425" stroke="#ff4d4d" stroke-width="2.5"/>'
            '</svg>'
            '<div style="margin-bottom: 15px; position: relative; z-index: 2;">'
            '<svg width="130" height="90" viewBox="0 0 200 130" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M25 25 Q 70 45 95 85 Q 55 105 15 95 Z" fill="#f8fafc" stroke="#0f172a" stroke-width="9" stroke-linejoin="round"/>'
            '<path d="M175 25 Q 130 45 105 85 Q 145 105 185 95 Z" fill="#f8fafc" stroke="#0f172a" stroke-width="9" stroke-linejoin="round"/>'
            '</svg>'
            '</div>'
            '<div style="position: relative; z-index: 2;">'
            '<div style="font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 1.5px; line-height: 1.25; font-family: Impact, sans-serif; text-shadow: 0 4px 12px rgba(0,0,0,0.9);">'
            'WITH GREAT <span style="color: #ff4d4d;">POWER</span><br>COMES GREAT <span style="color: #ff4d4d;">RESPONSIBILITY</span>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # SECURE LOGIN FORM BOX
        # ----------------------------------------------------

        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px 25px; margin-top: 10px;">'
            '<div style="font-size: 20px; font-weight: 800; color: #ffffff; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">🔐 <span>Secure Login</span></div>'
            '<div style="color: #94a3b8; font-size: 13px; margin-bottom: 15px;">Login to access your official or citizen portal.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        email = st.text_input("Email", placeholder="Enter your email", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

        if st.button("Login", type="primary", use_container_width=True):
            entered_email = email.strip().lower()
            entered_password = password.strip()

            if not entered_email:
                st.error("Please enter your email.")
            elif not entered_password:
                st.error("Please enter your password.")
            else:
                user = USERS.get(entered_email)
                if user is None:
                    st.error("User account not found.")
                elif entered_password != user["password"]:
                    st.error("Incorrect password.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user["role"]
                    st.session_state.user_email = entered_email
                    st.rerun()

        # ----------------------------------------------------
        # QUICK DEMO LOGIN BUTTONS
        # ----------------------------------------------------

        st.markdown(
            '<div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.08);">'
            '<div style="font-size: 13px; font-weight: 700; color: #cbd5e1; margin-bottom: 10px;">⚡ Quick Demo Login</div>'
            '</div>',
            unsafe_allow_html=True
        )

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if st.button("🏛️ Government Official", type="secondary", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.user_role = "Government Official"
                st.session_state.user_email = "official@gov.in"
                st.rerun()
            st.caption("`official@gov.in` | `official123`")

        with d_col2:
            if st.button("👤 Citizen Portal", type="secondary", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.user_role = "Citizen"
                st.session_state.user_email = "citizen@gov.in"
                st.rerun()
            st.caption("`citizen@gov.in` | `citizen123`")


    # --------------------------------------------------------
    # 3. OUR PLATFORM - FEATURE CARDS (3x2 GRID)
    # --------------------------------------------------------

    st.markdown(
        '<div style="text-align: center; margin: 65px 0px 35px 0px;">'
        '<div style="color: #e63946; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Our Platform</div>'
        '<h2 style="font-size: 36px; font-weight: 800; color: #ffffff; margin-top: 6px; font-family: Georgia, serif;">Intelligent. Transparent. Responsible.</h2>'
        '<div style="width: 55px; height: 3px; background: #e63946; margin: 12px auto 0px auto; border-radius: 2px;"></div>'
        '</div>',
        unsafe_allow_html=True
    )

    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; height: 190px; margin-bottom: 20px;">'
            '<div style="font-size: 30px; margin-bottom: 12px;">🏛️</div>'
            '<div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">Smart Governance</div>'
            '<div style="font-size: 13.5px; color: #94a3b8; line-height: 1.5;">AI-driven insights for better policy making and resource allocation.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; height: 190px; margin-bottom: 20px;">'
            '<div style="font-size: 30px; margin-bottom: 12px;">📢</div>'
            '<div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">Announcements</div>'
            '<div style="font-size: 13.5px; color: #94a3b8; line-height: 1.5;">Stay informed with the latest news, updates and announcements.</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with f_col2:
        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; height: 190px; margin-bottom: 20px;">'
            '<div style="font-size: 30px; margin-bottom: 12px;">💬</div>'
            '<div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">Complaint Management</div>'
            '<div style="font-size: 13.5px; color: #94a3b8; line-height: 1.5;">Easy submission, tracking and resolution of citizen complaints.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; height: 190px; margin-bottom: 20px;">'
            '<div style="font-size: 30px; margin-bottom: 12px;">👥</div>'
            '<div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">Citizen Engagement</div>'
            '<div style="font-size: 13.5px; color: #94a3b8; line-height: 1.5;">Strengthening trust through transparency and citizen participation.</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with f_col3:
        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; height: 190px; margin-bottom: 20px;">'
            '<div style="font-size: 30px; margin-bottom: 12px;">📈</div>'
            '<div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">Analytics &amp; Predictions</div>'
            '<div style="font-size: 13.5px; color: #94a3b8; line-height: 1.5;">Advanced analytics and predictions for proactive decision making.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="background: #131927; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; height: 190px; margin-bottom: 20px;">'
            '<div style="font-size: 30px; margin-bottom: 12px;">🛡️</div>'
            '<div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">Secure &amp; Reliable</div>'
            '<div style="font-size: 13.5px; color: #94a3b8; line-height: 1.5;">Enterprise grade security ensuring your data is safe and confidential.</div>'
            '</div>',
            unsafe_allow_html=True
        )


    # --------------------------------------------------------
    # 4. MOTIVATIONAL QUOTE BANNER
    # --------------------------------------------------------

    st.markdown(
        '<div style="background: linear-gradient(180deg, rgba(19, 25, 39, 0.85) 0%, rgba(11, 15, 23, 0.98) 100%), url(https://images.unsplash.com/photo-1561361513-2d000a50f0dc?q=80&w=1200&auto=format&fit=crop); background-size: cover; background-position: center; border-radius: 18px; padding: 55px 30px; text-align: center; border: 1px solid rgba(255,255,255,0.08); margin: 45px 0px 40px 0px; position: relative;">'
        '<div style="font-size: 55px; color: #e63946; font-family: Georgia, serif; line-height: 0.8; margin-bottom: 10px;">“</div>'
        '<div style="font-size: 34px; font-weight: 800; color: #ffffff; font-family: Georgia, serif; letter-spacing: 0.5px;">Incredible India, Intelligent Future.</div>'
        '<div style="font-size: 16px; color: #e63946; font-weight: 700; margin-top: 12px; letter-spacing: 1.5px;">— Towards Viksit Bharat</div>'
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # 5. FOOTER
    # --------------------------------------------------------

    st.markdown(
        '<div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 25px; margin-top: 40px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; color: #64748b; font-size: 13px;">'
        '<div style="display: flex; align-items: center; gap: 10px;">'
        '<span>🏛️</span>'
        '<span>© 2026 Government of India. All rights reserved.</span>'
        '</div>'
        '<div style="display: flex; gap: 20px; font-weight: 500;">'
        '<span style="color: #94a3b8; cursor: pointer;">Privacy Policy ▾</span>'
        '<span style="color: #94a3b8; cursor: pointer;">Terms of Service ▾</span>'
        '<span style="color: #94a3b8; cursor: pointer;">Contact Us</span>'
        '</div>'
        '<div style="display: flex; gap: 15px; font-size: 16px; color: #94a3b8;">'
        '<span>🌐</span>'
        '<span>📢</span>'
        '<span>🛡️</span>'
        '<span>🏛️</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# GOVERNMENT OFFICIAL PORTAL
# ============================================================

def open_government_portal():
    try:
        from official_app import show_official_portal
        show_official_portal()
    except Exception as e:
        st.error("Unable to load Government Official Portal.")
        st.code(str(e))


# ============================================================
# CITIZEN PORTAL
# ============================================================

def open_citizen_portal():
    try:
        from citizen_portal import show_citizen_portal
        show_citizen_portal()
    except Exception as e:
        st.error("Unable to load Citizen Portal.")
        st.code(str(e))


# ============================================================
# LOGOUT
# ============================================================

def logout():
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None

    if "login_email" in st.session_state:
        del st.session_state["login_email"]

    if "login_password" in st.session_state:
        del st.session_state["login_password"]

    st.rerun()


# ============================================================
# PORTAL ROUTER
# ============================================================

def open_portal():
    role = st.session_state.get("user_role")

    if role == "Government Official":
        open_government_portal()
    elif role == "Citizen":
        open_citizen_portal()
    else:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_email = None
        st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    if st.session_state.logged_in:
        open_portal()
    else:
        login_page()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    main()