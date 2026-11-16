import streamlit as st
from app.utils.locations import STATE_DISTRICT_MAP

try:
    from app.frontend.utils.api import submit_complaint, classify_image_api
except ImportError:
    from utils.api import submit_complaint, classify_image_api

CATEGORY_ICONS = {
    "road_damage": "🛣️",
    "garbage": "🗑️",
    "streetlights": "💡",
    "water_supply": "🚰",
    "electricity": "⚡",
    "traffic_safety": "🚦",
    "sewerage": "🕳️"
}


def show():
    st.title("📝 Submit Complaint")
    st.write("Report a civic issue by describing it below and optionally uploading photo evidence for instant AI verification.")

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

    # --------------------------------------------------------
    # PHOTO EVIDENCE UPLOAD & DEEP LEARNING CLASSIFICATION
    # --------------------------------------------------------
    st.subheader("📷 Photo Evidence (Deep Learning Verified)")
    uploaded_file = st.file_uploader(
        "Upload a photo of the issue (optional)",
        type=["jpg", "jpeg", "png"],
        help="Upload photo evidence of potholes, garbage, streetlights, water supply, electricity hazards, traffic safety, or open sewerage."
    )

    image_meta = None
    if uploaded_file is not None:
        file_key = f"dl_cache_{uploaded_file.name}_{uploaded_file.size}"
        if file_key not in st.session_state:
            with st.spinner("Analyzing photo with MobileNetV2 Deep Learning model..."):
                img_bytes = uploaded_file.getvalue()
                analysis = classify_image_api(img_bytes, filename=uploaded_file.name)
                st.session_state[file_key] = analysis

        image_meta = st.session_state.get(file_key)

        # Visual layout for photo & prediction
        img_col, info_col = st.columns([1, 2])
        with img_col:
            st.image(uploaded_file, caption="Uploaded Evidence", use_container_width=True)

        with info_col:
            if image_meta and "error" not in image_meta:
                pred_class = image_meta.get("predicted_class", "")
                icon = CATEGORY_ICONS.get(pred_class, "🔍")
                disp_name = image_meta.get("display_name", pred_class.replace("_", " ").title())
                conf = image_meta.get("confidence", 0)

                st.markdown(f"### {icon} {disp_name}")
                st.progress(min(1.0, conf / 100.0), text=f"AI Confidence: **{conf}%**")

                c_dep, c_sla, c_prio = st.columns(3)
                with c_dep:
                    st.caption("Suggested Department")
                    st.markdown(f"**{image_meta.get('suggested_department', 'BBMP')}**")
                with c_sla:
                    st.caption("Estimated SLA")
                    st.markdown(f"**{image_meta.get('sla_hours', 24)} hours**")
                with c_prio:
                    st.caption("Priority")
                    st.markdown(f"**{image_meta.get('suggested_priority', 'Medium')}**")

                if image_meta.get("description"):
                    st.info(f"💡 {image_meta['description']}")

                # Quick button to auto-fill description
                default_prompt = f"Reporting an issue regarding {disp_name.lower()} in {district}, {state}. Please dispatch the concerned team."
                if st.button("✨ Use AI Suggestion as Complaint Description"):
                    st.session_state["complaint_text_input"] = default_prompt
                    st.rerun()

            elif image_meta and "error" in image_meta:
                st.warning(f"Could not classify image: {image_meta['error']}")

    # --------------------------------------------------------
    # COMPLAINT DESCRIPTION
    # --------------------------------------------------------
    prefilled_text = st.session_state.get("complaint_text_input", "")
    complaint = st.text_area(
        "Complaint Description",
        value=prefilled_text,
        height=160,
        placeholder="Example: There is a deep pothole on the main road causing severe traffic congestion and two-wheeler accidents."
    )

    if st.button("🚀 Submit Complaint", type="primary"):
        if complaint.strip() == "":
            st.error("Please enter your complaint description.")
        else:
            with st.spinner("Submitting complaint and running AI analysis..."):
                result = submit_complaint(
                    text=complaint.strip(),
                    state=state,
                    district=district,
                    image_meta=image_meta if (image_meta and "error" not in image_meta) else None
                )

            if "error" in result:
                st.error(result["error"])
            else:
                complaint_number = result.get(
                    "complaint_number",
                    "Not available"
                )
                dept = result.get("department", "Concerned Department")
                prio = result.get("priority", "Normal")
                storage_status = result.get("storage_status", "unknown")
                is_persisted = (storage_status == "persisted_in_database") and not str(complaint_number).startswith("OFFLINE-")

                if is_persisted:
                    st.success("✅ Official Complaint Registered in Government Database!")
                    st.info(f"""
### 🏛️ Official Tracking ID: `{complaint_number}`

- **Routed Department:** {dept}
- **Assigned Priority:** {prio}
- **Location:** {district}, {state}
{"- **Visual Evidence Verified:** " + image_meta['display_name'] + " (" + str(image_meta['confidence']) + "% confidence)" if (image_meta and 'display_name' in image_meta) else ""}

Your complaint has been officially registered in the central citizen database and routed to the nodal officer. You can track live updates on the **Track Status** tab using your Tracking ID.
""")
                else:
                    st.warning("⚠️ Central Database Offline – Saved as Local Citizen Draft")
                    st.markdown(f"""
### 📝 Local Draft Reference: `{complaint_number}`

> **Important Notice:** The central grievance database is currently unreachable. Your AI analysis and complaint details have been processed and saved locally as a draft, but **this complaint is not yet officially registered with government nodal officers.**

**AI Triage Summary:**
- **Recommended Department:** {dept}
- **Assigned Priority:** {prio}
- **Location:** {district}, {state}
{"- **Visual Evidence Verified:** " + image_meta['display_name'] + " (" + str(image_meta['confidence']) + "% confidence)" if (image_meta and 'display_name' in image_meta) else ""}

**Next Steps for Citizen:**
1. Please save your Draft Reference ID: `{complaint_number}`.
2. When database connectivity is restored, click **Submit Complaint** again or contact your local municipal helpline.
""")
