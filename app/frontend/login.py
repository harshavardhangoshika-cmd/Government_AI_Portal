import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))


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
# LOGIN PAGE
# ============================================================

def login_page():

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            text-align: center;
            padding-top: 50px;
            padding-bottom: 25px;
        ">

            <div style="
                font-size: 60px;
            ">
                🏛️
            </div>

            <h1>
                Government AI Portal
            </h1>

            <p style="
                color: #9ca3af;
                font-size: 18px;
            ">
                AI-Powered Citizen & Government
                Intelligence Platform
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # LOGIN BOX
    # --------------------------------------------------------

    left, center, right = st.columns([1, 2, 1])

    with center:

        st.subheader("🔐 Secure Login")

        st.write(
            "Login to access your portal."
        )


        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        email = st.text_input(
            "Email",
            placeholder="Enter your email",
            key="login_email"
        )


        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )


        st.write("")


        # ----------------------------------------------------
        # LOGIN BUTTON
        # ----------------------------------------------------

        if st.button(
            "Login",
            type="primary",
            use_container_width=True
        ):

            entered_email = email.strip().lower()
            entered_password = password.strip()


            # ------------------------------------------------
            # EMPTY EMAIL
            # ------------------------------------------------

            if not entered_email:

                st.error(
                    "Please enter your email."
                )

                return


            # ------------------------------------------------
            # EMPTY PASSWORD
            # ------------------------------------------------

            if not entered_password:

                st.error(
                    "Please enter your password."
                )

                return


            # ------------------------------------------------
            # FIND USER
            # ------------------------------------------------

            user = USERS.get(
                entered_email
            )


            if user is None:

                st.error(
                    "User account not found."
                )

                return


            # ------------------------------------------------
            # CHECK PASSWORD
            # ------------------------------------------------

            if entered_password != user["password"]:

                st.error(
                    "Incorrect password."
                )

                return


            # ------------------------------------------------
            # LOGIN SUCCESS
            # ------------------------------------------------

            st.session_state.logged_in = True

            st.session_state.user_role = (
                user["role"]
            )

            st.session_state.user_email = (
                entered_email
            )

            st.rerun()


        # ----------------------------------------------------
        # DEMO ACCOUNTS
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "Demo Accounts"
        )


        col1, col2 = st.columns(2)


        # ----------------------------------------------------
        # GOVERNMENT OFFICIAL ACCOUNT
        # ----------------------------------------------------

        with col1:

            st.markdown(
                """
                ### 🏛️ Government Official

                *Email*

                official@gov.in

                *Password*

                official123
                """
            )

            if st.button("🚀 Enter Official Portal (Demo)", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.user_role = "Government Official"
                st.session_state.user_email = "official@gov.in"
                st.rerun()


        # ----------------------------------------------------
        # CITIZEN ACCOUNT
        # ----------------------------------------------------

        with col2:

            st.markdown(
                """
                ### 👤 Citizen

                *Email*

                citizen@gov.in

                *Password*

                citizen123
                """
            )

            if st.button("🚀 Enter Citizen Portal (Demo)", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.user_role = "Citizen"
                st.session_state.user_email = "citizen@gov.in"
                st.rerun()


# ============================================================
# GOVERNMENT OFFICIAL PORTAL
# ============================================================

def open_government_portal():

    try:

        from official_app import show_official_portal

        show_official_portal()

    except Exception as e:

        st.error(
            "Unable to load Government Official Portal."
        )

        st.code(
            str(e)
        )


# ============================================================
# CITIZEN PORTAL
# ============================================================

def open_citizen_portal():

    try:

        from citizen_portal import show_citizen_portal

        show_citizen_portal()

    except Exception as e:

        st.error(
            "Unable to load Citizen Portal."
        )

        st.code(
            str(e)
        )


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False

    st.session_state.user_role = None

    st.session_state.user_email = None


    # Remove login fields

    if "login_email" in st.session_state:

        del st.session_state["login_email"]


    if "login_password" in st.session_state:

        del st.session_state["login_password"]


    st.rerun()


# ============================================================
# PORTAL ROUTER
# ============================================================

def open_portal():

    role = st.session_state.get(
        "user_role"
    )


    # --------------------------------------------------------
    # GOVERNMENT OFFICIAL
    # --------------------------------------------------------

    if role == "Government Official":

        open_government_portal()


    # --------------------------------------------------------
    # CITIZEN
    # --------------------------------------------------------

    elif role == "Citizen":

        open_citizen_portal()


    # --------------------------------------------------------
    # INVALID ROLE
    # --------------------------------------------------------

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