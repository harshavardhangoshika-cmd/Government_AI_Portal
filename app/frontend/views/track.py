import streamlit as st
try:
    from app.frontend.utils.api import track_complaint
except ImportError:
    from utils.api import track_complaint


def show():

    st.title("🔍 Track Complaint")

    st.write("Enter your Complaint ID to check the current status.")

    complaint_number = st.text_input(
        "Complaint ID",
        placeholder="Example: GC-2026-000003"
    )

    if st.button("Track Complaint"):

        if complaint_number.strip() == "":
            st.error("Please enter your Complaint ID.")

        else:

            with st.spinner("Checking complaint status..."):

                result = track_complaint(
                    complaint_number.strip()
                )

            if "error" in result:

                st.error(result["error"])

            else:

                st.success("Complaint found!")

                st.subheader(
                    f"Complaint ID: {result.get('complaint_number')}"
                )

                st.write(
                    f"**Department:** "
                    f"{result.get('department') or 'Not assigned yet'}"
                )

                st.write(
                    f"**Current Status:** "
                    f"{result.get('status') or 'Submitted'}"
                )

                st.divider()

                st.subheader("Complaint Progress")

                status = result.get("status") or "Submitted"

                statuses = [
                    "Submitted",
                    "Assigned",
                    "Under Review",
                    "Field Inspection",
                    "Resolved"
                ]

                current_index = (
                    statuses.index(status)
                    if status in statuses
                    else 0
                )

                for i, item in enumerate(statuses):

                    if i <= current_index:
                        st.success(f"✔ {item}")
                    else:
                        st.write(f"⬜ {item}")

                if result.get("officer_remarks"):
                    st.divider()
                    st.subheader("Official Update")
                    st.info(result["officer_remarks"])