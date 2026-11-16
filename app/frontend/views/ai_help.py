import streamlit as st

try:
    from app.frontend.utils.api import query_rag_api
except ImportError:
    from utils.api import query_rag_api


SUGGESTED_PROMPTS = [
    "🛣️ How to report potholes and what is the official SLA?",
    "🕳️ Emergency rules for open manholes and sewage leaks",
    "⚡ BESCOM guidelines for live hanging wires & outages",
    "☀️ How much subsidy can I get under PM Surya Ghar solar?",
    "📜 What compensation can I claim under Karnataka Sakala Act?",
    "🏠 Who is eligible for PMAY housing scheme?"
]


def show():
    st.title("🤖 Citizen AI Assistant & Grievance Guide")
    st.caption("Powered by Civic RAG • Authoritative municipal SLAs, bylaws, government schemes, and escalation guidance.")

    # Sidebar / Knowledge info
    with st.expander("ℹ️ About the Government Civic Knowledge Base", expanded=False):
        st.markdown("""
        This AI assistant retrieves verified guidelines directly from:
        - **Municipal Acts:** KMC Act, Solid Waste Management Rules 2016, IRC Standards.
        - **Service Guarantees:** Karnataka Sakala Services Act (Statutory SLAs & Delay Compensation).
        - **Welfare Schemes:** PM Surya Ghar (Rooftop Solar), PMAY (Housing), Jal Jeevan Mission, AMRUT 2.0.
        - **Civic Authorities:** BBMP, BWSSB, BESCOM, Traffic Police, DARPG (CPGRAMS).
        """)

    # Initialize Chat History
    if "rag_chat_messages" not in st.session_state:
        st.session_state["rag_chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "👋 **Namaste! I am your Government Civic AI Assistant.**\n\n"
                    "You can ask me about:\n"
                    "- **Official resolution timelines (SLAs)** for road damage, garbage, water leaks, power cuts, etc.\n"
                    "- **Government welfare schemes** (PM Surya Ghar Solar, PMAY Housing, Har Ghar Jal).\n"
                    "- **Escalation procedures** if municipal officers miss statutory deadlines.\n"
                    "- **Live tracking** for your complaint ID (e.g., `CMP-...`).\n\n"
                    "How can I help you today?"
                ),
                "sources": []
            }
        ]

    # Quick prompt selection chips
    st.write("##### 💡 Suggested Questions")
    cols = st.columns(3)
    clicked_prompt = None
    for idx, prompt in enumerate(SUGGESTED_PROMPTS):
        col = cols[idx % 3]
        if col.button(prompt, key=f"chip_{idx}", use_container_width=True):
            clicked_prompt = prompt

    st.divider()

    # Display Chat History
    for msg in st.session_state["rag_chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Verified Citations & References", expanded=False):
                    for src in msg["sources"]:
                        st.markdown(
                            f"- **[{src.get('id')}] {src.get('topic')}**  \n"
                            f"  *Authority:* {src.get('authority')} | *Act:* {src.get('act_or_scheme')} | *SLA:* `{src.get('sla_hours')} hrs`"
                        )

    # Handle input from chat_input or chip click
    user_query = st.chat_input("Ask a question about civic issues, SLAs, or government schemes...")
    if clicked_prompt and not user_query:
        # Strip emoji from start for clean query
        user_query = clicked_prompt.split(" ", 1)[-1]

    if user_query:
        # Append User Message
        st.session_state["rag_chat_messages"].append({
            "role": "user",
            "content": user_query
        })
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Searching Civic Knowledge Base & Government Charters..."):
                res = query_rag_api(user_query)

                if "error" in res:
                    ans_text = f"⚠️ {res['error']}"
                    sources = []
                else:
                    ans_text = res.get("answer", "No answer found.")
                    sources = res.get("sources", [])

                st.markdown(ans_text)

                if sources:
                    with st.expander("📚 Verified Citations & References", expanded=True):
                        for src in sources:
                            st.markdown(
                                f"- **[{src.get('id')}] {src.get('topic')}**  \n"
                                f"  *Authority:* {src.get('authority')} | *Act:* {src.get('act_or_scheme')} | *SLA:* `{src.get('sla_hours')} hrs`"
                            )

        # Save Assistant Message
        st.session_state["rag_chat_messages"].append({
            "role": "assistant",
            "content": ans_text,
            "sources": sources
        })

    # Clear chat option
    if len(st.session_state["rag_chat_messages"]) > 1:
        if st.sidebar.button("🗑️ Clear Chat History"):
            st.session_state["rag_chat_messages"] = [st.session_state["rag_chat_messages"][0]]
            st.rerun()
