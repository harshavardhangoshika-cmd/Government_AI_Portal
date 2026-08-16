import streamlit as st
from app.utils.locations import STATE_DISTRICT_MAP

try:
    from app.frontend.utils.api import submit_complaint
except ImportError:
    from utils.api import submit_complaint


def show():

    st.title("📝 Submit Complaint")

    st.write("Please select your location and describe your complaint below.")

    col1, col2 = st.columns(2)
    with col1:
        state_list = list(STATE_DISTRICT_MAP.keys())
        state = st.selectbox(
            "State / UT",
            state_list,
            index=0
        )
    with col2:
        available_districts = STATE_DISTRICT_MAP.get(state, ["Bengaluru Urban"])
        district = st.selectbox("District", available_districts, index=0)

    complaint = st.text_area(
        "Complaint Description",
        height=180,
        placeholder="Example: There has been no water supply in our area for the last five days."
    )

    if st.button("Submit Complaint"):

        if complaint.strip() == "":
            st.error("Please enter your complaint.")

        else:

            with st.spinner("Submitting complaint..."):

                result = submit_complaint(
                    text=complaint.strip(),
                    state=state,
                    district=district
                )

            if "error" in result:

                st.error(result["error"])

            else:

                st.success("✅ Complaint Submitted Successfully!")

                complaint_number = result.get(
                    "complaint_number",
                    "Not available"
                )

                st.info(f"""
**Complaint ID**

### {complaint_number}

Your complaint has been forwarded to the appropriate government department.

You can track its status using the Complaint ID.
""")