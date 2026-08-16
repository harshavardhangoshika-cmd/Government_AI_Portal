import streamlit as st

def show():

    st.title("🏛 Government Citizen Intelligence System")

    st.markdown("""
    ### Welcome!

    This portal helps citizens submit complaints and track their status easily.

    Using Artificial Intelligence, complaints are analyzed and sent to the appropriate government department for faster processing.
    """)

    st.warning("""
    ⚠ AI Notice

    Complaint classifications are generated using Artificial Intelligence.

    AI predictions may sometimes be incorrect.

    All complaints are reviewed and processed by the appropriate government department before any official action is taken.
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.info("📝 Submit a new complaint quickly.")

    with col2:
        st.info("🔍 Track your complaint status anytime.")