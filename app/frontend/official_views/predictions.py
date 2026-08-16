import streamlit as st
import pandas as pd


# ============================================================
# DATABASE
# ============================================================
from app.database.database import supabase


# ============================================================
# GOVERNMENT COMPLAINTS
# ============================================================

def show():

    # ========================================================
    # PAGE HEADER
    # ========================================================

    st.title(
        "📋 Government Complaints"
    )

    st.write(
        "View, search, and filter citizen complaints "
        "received by the government."
    )

    st.markdown("---")


    # ========================================================
    # LOAD COMPLAINTS
    # ========================================================

    try:

        response = (
            supabase
            .table("complaints")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        complaints = response.data or []

    except Exception as e:

        st.error(
            "Unable to load complaints from database."
        )

        st.code(
            str(e)
        )

        return


    # ========================================================
    # NO COMPLAINTS
    # ========================================================

    if not complaints:

        st.info(
            "No complaints found."
        )

        return


    # ========================================================
    # DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        complaints
    )


    # ========================================================
    # HELPER FUNCTION
    # ========================================================

    def get_column(row, *names, default="-"):

        for name in names:

            if name in row:

                value = row.get(name)

                if value is not None and value != "":

                    return value

        return default


    # ========================================================
    # SEARCH & FILTERS
    # ========================================================

    st.subheader(
        "🔍 Search & Filters"
    )


    # --------------------------------------------------------
    # COMPLAINT ID / DEPARTMENT / STATUS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        complaint_search = st.text_input(
            "Complaint ID",
            placeholder="Example: GC-2026-000007"
        )


    # --------------------------------------------------------
    # DEPARTMENT OPTIONS
    # --------------------------------------------------------

    departments = []

    if "department" in df.columns:

        departments = sorted(
            [
                str(x)
                for x in df["department"]
                .dropna()
                .unique()
                if str(x).strip()
            ]
        )


    with col2:

        selected_department = st.selectbox(
            "Department",
            ["All"] + departments
        )


    # --------------------------------------------------------
    # STATUS OPTIONS
    # --------------------------------------------------------

    statuses = []

    if "status" in df.columns:

        statuses = sorted(
            [
                str(x)
                for x in df["status"]
                .dropna()
                .unique()
                if str(x).strip()
            ]
        )


    with col3:

        selected_status = st.selectbox(
            "Status",
            ["All"] + statuses
        )


    # --------------------------------------------------------
    # PRIORITY / EMERGENCY
    # --------------------------------------------------------

    col4, col5 = st.columns(2)


    # --------------------------------------------------------
    # PRIORITY OPTIONS
    # --------------------------------------------------------

    priorities = []

    priority_columns = [
        "priority",
        "priority_level"
    ]

    for column in priority_columns:

        if column in df.columns:

            priorities = sorted(
                [
                    str(x)
                    for x in df[column]
                    .dropna()
                    .unique()
                    if str(x).strip()
                ]
            )

            break


    with col4:

        selected_priority = st.selectbox(
            "Priority",
            ["All"] + priorities
        )


    # --------------------------------------------------------
    # EMERGENCY OPTIONS
    # --------------------------------------------------------

    with col5:

        selected_emergency = st.selectbox(
            "Emergency",
            [
                "All",
                "Emergency",
                "Not Emergency"
            ]
        )


    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_complaints = []


    for complaint in complaints:

        # ----------------------------------------------------
        # COMPLAINT ID
        # ----------------------------------------------------

        complaint_id = str(
            get_column(
                complaint,
                "complaint_number",
                "complaint_id",
                "id",
                default=""
            )
        )


        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        department = str(
            get_column(
                complaint,
                "department",
                default=""
            )
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = str(
            get_column(
                complaint,
                "status",
                default=""
            )
        )


        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        priority = str(
            get_column(
                complaint,
                "priority",
                "priority_level",
                default=""
            )
        )


        # ----------------------------------------------------
        # EMERGENCY
        # ----------------------------------------------------

        emergency_value = get_column(
            complaint,
            "emergency",
            "is_emergency",
            default=0
        )


        # ----------------------------------------------------
        # COMPLAINT ID SEARCH
        # ----------------------------------------------------

        if complaint_search:

            if complaint_search.lower() not in complaint_id.lower():

                continue


        # ----------------------------------------------------
        # DEPARTMENT FILTER
        # ----------------------------------------------------

        if selected_department != "All":

            if department != selected_department:

                continue


        # ----------------------------------------------------
        # STATUS FILTER
        # ----------------------------------------------------

        if selected_status != "All":

            if status != selected_status:

                continue


        # ----------------------------------------------------
        # PRIORITY FILTER
        # ----------------------------------------------------

        if selected_priority != "All":

            if priority != selected_priority:

                continue


        # ----------------------------------------------------
        # EMERGENCY FILTER
        # ----------------------------------------------------

        emergency_bool = False

        if str(emergency_value).lower() in [
            "1",
            "true",
            "yes",
            "emergency"
        ]:

            emergency_bool = True


        if selected_emergency == "Emergency":

            if not emergency_bool:

                continue


        elif selected_emergency == "Not Emergency":

            if emergency_bool:

                continue


        # ----------------------------------------------------
        # ADD COMPLAINT
        # ----------------------------------------------------

        filtered_complaints.append(
            complaint
        )


    # ========================================================
    # VIEW COMPLAINT DETAILS
    # ========================================================

    st.markdown("---")

    st.subheader(
        "👁️ View Complaint Details"
    )


    # ========================================================
    # COMPLAINT OPTIONS
    # ========================================================

    complaint_options = []


    for complaint in filtered_complaints:

        complaint_id = get_column(
            complaint,
            "complaint_number",
            "complaint_id",
            "id",
            default="-"
        )

        complaint_options.append(
            str(complaint_id)
        )


    # Remove duplicates while preserving order

    complaint_options = list(
        dict.fromkeys(
            complaint_options
        )
    )


    # ========================================================
    # SELECT COMPLAINT
    # ========================================================

    if complaint_options:

        selected_complaint_id = st.selectbox(
            "Select Complaint",
            complaint_options
        )


        # ----------------------------------------------------
        # FIND SELECTED COMPLAINT
        # ----------------------------------------------------

        selected_complaint = None


        for complaint in filtered_complaints:

            complaint_id = str(
                get_column(
                    complaint,
                    "complaint_number",
                    "complaint_id",
                    "id",
                    default="-"
                )
            )

            if complaint_id == selected_complaint_id:

                selected_complaint = complaint

                break


        # ====================================================
        # DISPLAY DETAILS
        # ====================================================

        if selected_complaint:

            st.markdown("---")


            # ------------------------------------------------
            # COMPLAINT ID
            # ------------------------------------------------

            st.header(
                f"Complaint ID: {selected_complaint_id}"
            )


            # ------------------------------------------------
            # DETAILS
            # ------------------------------------------------

            col1, col2 = st.columns(2)


            with col1:

                st.write(
                    f"**Department:** "
                    f"{get_column(selected_complaint, 'department')}"
                )

                st.write(
                    f"**Status:** "
                    f"{get_column(selected_complaint, 'status')}"
                )

                st.write(
                    f"**Priority:** "
                    f"{get_column(selected_complaint, 'priority', 'priority_level')}"
                )


            with col2:

                st.write(
                    f"**Emergency:** "
                    f"{get_column(selected_complaint, 'emergency', 'is_emergency', default=0)}"
                )

                st.write(
                    f"**State:** "
                    f"{get_column(selected_complaint, 'state')}"
                )

                st.write(
                    f"**District:** "
                    f"{get_column(selected_complaint, 'district')}"
                )


            # ------------------------------------------------
            # COMPLAINT TEXT
            # ------------------------------------------------

            st.markdown("### 📝 Complaint")


            complaint_text = get_column(
                selected_complaint,
                "complaint_text",
                "description",
                "complaint",
                "details",
                "message",
                default="-"
            )


            st.write(
                complaint_text
            )


            # ------------------------------------------------
            # AI CLASSIFICATION
            # ------------------------------------------------

            st.markdown(
                "### 🤖 AI Classification"
            )


            col1, col2 = st.columns(2)


            with col1:

                st.write(
                    f"**Sentiment:** "
                    f"{get_column(selected_complaint, 'sentiment')}"
                )

                st.write(
                    f"**Feedback Category:** "
                    f"{get_column(selected_complaint, 'feedback_category', 'feedback')}"
                )

                st.write(
                    f"**Complaint Reason:** "
                    f"{get_column(selected_complaint, 'complaint_reason', 'reason')}"
                )


            with col2:

                st.write(
                    f"**Department:** "
                    f"{get_column(selected_complaint, 'department')}"
                )

                st.write(
                    f"**Priority:** "
                    f"{get_column(selected_complaint, 'priority', 'priority_level')}"
                )

                st.write(
                    f"**Emergency:** "
                    f"{get_column(selected_complaint, 'emergency', 'is_emergency', default=0)}"
                )


    else:

        st.info(
            "No complaints match the selected filters."
        )


    # ========================================================
    # COMPLAINT TABLE
    # ========================================================

    st.markdown("---")

    st.subheader(
        f"📊 Complaints Found: {len(filtered_complaints)}"
    )


    # ========================================================
    # PREPARE TABLE DATA
    # ========================================================

    table_data = []


    for complaint in filtered_complaints:

        # ----------------------------------------------------
        # COMPLAINT ID
        # ----------------------------------------------------

        complaint_id = get_column(
            complaint,
            "complaint_number",
            "complaint_id",
            "id",
            default="-"
        )


        # ----------------------------------------------------
        # COMPLAINT TEXT
        # ----------------------------------------------------

        complaint_text = get_column(
            complaint,
            "complaint_text",
            "description",
            "complaint",
            "details",
            "message",
            default="-"
        )


        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        department = get_column(
            complaint,
            "department",
            default="-"
        )


        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        priority = get_column(
            complaint,
            "priority",
            "priority_level",
            default="-"
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = get_column(
            complaint,
            "status",
            default="-"
        )


        # ----------------------------------------------------
        # EMERGENCY
        # ----------------------------------------------------

        emergency = get_column(
            complaint,
            "emergency",
            "is_emergency",
            default=0
        )


        # ----------------------------------------------------
        # SENTIMENT
        # ----------------------------------------------------

        sentiment = get_column(
            complaint,
            "sentiment",
            default="-"
        )


        # ----------------------------------------------------
        # TABLE ROW
        # ----------------------------------------------------

        table_data.append(
            {
                "Complaint ID":
                    complaint_id,

                "Complaint":
                    complaint_text,

                "Department":
                    department,

                "Priority":
                    priority,

                "Status":
                    status,

                "Emergency":
                    emergency,

                "Sentiment":
                    sentiment
            }
        )


    # ========================================================
    # DISPLAY TABLE
    # ========================================================

    table_df = pd.DataFrame(
        table_data,
        columns=[
            "Complaint ID",
            "Complaint",
            "Department",
            "Priority",
            "Status",
            "Emergency",
            "Sentiment"
        ]
    )


    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=500
    )