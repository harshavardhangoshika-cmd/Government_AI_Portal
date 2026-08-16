import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests

from app.database.database import get_all_complaints
from app.utils.sla_engine import enrich_complaints_with_sla

API_URL = "http://127.0.0.1:8000"

from app.utils.locations import DISTRICT_COORDS


def fetch_complaints():
    """Fetch complaints from API or database with SLA enrichment fallback."""
    try:
        res = requests.get(f"{API_URL}/government/complaints", timeout=5)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception:
        pass
    raw = get_all_complaints() or []
    return enrich_complaints_with_sla(raw)


def show():
    st.title("📍 Location Map & District Hotspot Engine")
    st.caption("Real-time district complaint mapping, baseline hotspot detection, and auto-generated supervisor reports.")

    # Apply Official Jurisdiction Scope
    jurisdiction_scope = st.session_state.get("official_jurisdiction", "All Jurisdictions (Statewide)")
    if jurisdiction_scope and jurisdiction_scope != "All Jurisdictions (Statewide)":
        st.info(f"🔒 **Jurisdiction Scope Active**: Displaying location map & hotspots for **{jurisdiction_scope}**.")

    st.divider()

    raw_complaints = fetch_complaints()

    if not raw_complaints:
        st.info("No complaint data available for geospatial analysis.")
        return

    district_names = list(DISTRICT_COORDS.keys())
    processed_data = []
    has_fallback_districts = False

    # Process all complaints and assign fallback district for legacy records
    for idx, c in enumerate(raw_complaints):
        dist = c.get("district")
        if not dist or str(dist).strip() == "" or str(dist).strip() in ["None", "null"]:
            dist = district_names[idx % len(district_names)]
            has_fallback_districts = True

        dist_clean = str(dist).strip()

        # Apply Jurisdiction Filter if scoped
        if jurisdiction_scope and jurisdiction_scope != "All Jurisdictions (Statewide)":
            if dist_clean.lower() != jurisdiction_scope.lower():
                continue

        processed_data.append({
            "complaint_id": c.get("complaint_number") or f"GC-{idx+1:06d}",
            "department": c.get("department") or "General",
            "priority": str(c.get("priority") or "Medium").capitalize(),
            "emergency": c.get("emergency") in [True, "true", "1", "yes", "Emergency"],
            "district": dist_clean,
            "created_at": c.get("created_at") or "Recently"
        })

    df = pd.DataFrame(processed_data, columns=["complaint_id", "department", "priority", "emergency", "district", "created_at"])

    if has_fallback_districts:
        st.caption("ℹ️ *Note: Some legacy complaints lacking explicit district metadata are distributed across Karnataka districts for visual demonstration purposes.*")

    # Count complaints per district safely
    counts_dict = {d: 0 for d in district_names}
    if not df.empty and "district" in df.columns:
        for d, cnt in df["district"].value_counts().items():
            counts_dict[str(d).strip()] = int(cnt)

    dist_counts = pd.DataFrame([
        {"district": d, "complaint_count": counts_dict.get(d, 0)}
        for d in district_names
    ])

    total_complaints = len(df)
    active_districts = len(district_names)
    baseline_avg = max(total_complaints / active_districts, 1.0)

    # Hotspot Algorithm Calculation
    dist_counts["baseline_avg"] = round(baseline_avg, 1)
    dist_counts["hotspot_ratio"] = (dist_counts["complaint_count"] / baseline_avg).round(2)

    def classify_hotspot(ratio):
        if ratio >= 2.0:
            return "🔴 Severe Hotspot"
        elif ratio >= 1.2:
            return "🟡 Moderate Hotspot"
        else:
            return "🟢 Normal Volume"

    dist_counts["severity"] = dist_counts["hotspot_ratio"].apply(classify_hotspot)
    dist_counts["lat"] = dist_counts["district"].apply(lambda d: DISTRICT_COORDS.get(d, {}).get("lat", 12.9716))
    dist_counts["lon"] = dist_counts["district"].apply(lambda d: DISTRICT_COORDS.get(d, {}).get("lon", 77.5946))

    # Top Hotspot District
    dist_counts_sorted = dist_counts.sort_values(by="complaint_count", ascending=False)
    top_district = dist_counts_sorted.iloc[0]

    # Metrics Summary Bar
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🗺️ Monitored Districts", active_districts)
    with m2:
        st.metric("📊 Baseline Avg / District", f"{baseline_avg:.1f}")
    with m3:
        severe_count = sum(dist_counts["severity"] == "🔴 Severe Hotspot")
        st.metric("🔴 Severe Hotspots", severe_count)
    with m4:
        top_name = top_district["district"]
        top_ratio = top_district["hotspot_ratio"]
        st.metric("⚡ Peak Hotspot", f"{top_name} ({top_ratio}x)")

    st.divider()

    # Auto-Generated Supervisor Summary Report
    st.subheader("📢 Auto-Generated Supervisor Summary Report")
    report_text = f"""
    > **STATUS REPORT**: **{top_district['district']}** is currently experiencing a **complaint activity level of {top_district['hotspot_ratio']}x** baseline average 
    > ({top_district['complaint_count']} total complaints vs {baseline_avg:.1f} average). Field deployment & priority action recommended.
    """
    st.markdown(report_text)

    st.divider()

    # Interactive Geospatial Map (Plotly Scattermapbox)
    st.subheader("🗺️ District Hotspot Geospatial Map")

    color_map = {
        "🔴 Severe Hotspot": "#EF4444",
        "🟡 Moderate Hotspot": "#F59E0B",
        "🟢 Normal Volume": "#10B981"
    }

    # Use constant size for map bubbles if counts are small so all district pins are visible
    dist_map_df = dist_counts.copy()
    dist_map_df["map_size"] = dist_map_df["complaint_count"].apply(lambda c: max(c, 5))

    fig_map = px.scatter_mapbox(
        dist_map_df,
        lat="lat",
        lon="lon",
        size="map_size",
        color="severity",
        color_discrete_map=color_map,
        hover_name="district",
        hover_data={"complaint_count": True, "hotspot_ratio": True, "map_size": False, "lat": False, "lon": False},
        size_max=35,
        zoom=6,
        center={"lat": 14.5000, "lon": 75.8000},
        mapbox_style="carto-positron",
        title="District Complaint Volume & Hotspot Severity Map"
    )
    fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=500)
    st.plotly_chart(fig_map, use_container_width=True)

    # Bar Breakdown & Hotspot Comparison Chart
    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        st.subheader("📊 District Hotspot Ratio vs Baseline (1.0x)")
        fig_bar = px.bar(
            dist_counts_sorted,
            x="district",
            y="hotspot_ratio",
            color="severity",
            color_discrete_map=color_map,
            labels={"hotspot_ratio": "Hotspot Ratio (x Baseline)", "district": "District"},
            text="hotspot_ratio"
        )
        fig_bar.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Baseline (1.0x)", annotation_position="top left")
        fig_bar.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_table:
        st.subheader("📋 Hotspot Ranking Table")
        st.dataframe(
            dist_counts_sorted[["district", "complaint_count", "hotspot_ratio", "severity"]],
            column_config={
                "district": "District",
                "complaint_count": "Complaints",
                "hotspot_ratio": "Hotspot Ratio",
                "severity": "Severity Level"
            },
            hide_index=True,
            use_container_width=True
        )

    # Department Breakdown per District
    st.divider()
    st.subheader("🏢 Department Breakdown by District")
    selected_district_detail = st.selectbox("Select District for Deep Dive", dist_counts_sorted["district"].tolist())

    district_df = df[df["district"] == selected_district_detail]
    if not district_df.empty:
        dept_counts = district_df["department"].value_counts().reset_index()
        dept_counts.columns = ["department", "count"]

        fig_dept = px.pie(
            dept_counts,
            names="department",
            values="count",
            title=f"Department Complaint Distribution - {selected_district_detail}",
            hole=0.4
        )
        fig_dept.update_layout(height=350)
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info(f"No active complaints logged for {selected_district_detail} under the current filter.")
