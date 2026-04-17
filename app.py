"""
Product Analytics Dashboard
Module-wise and company-wise activity insights with financial year (Apr-Mar) filtering.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import uuid
from datetime import datetime

try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

# Page config
st.set_page_config(page_title="Product Analytics Dashboard", page_icon="📊", layout="wide")

# Path to Excel files (same directory as app)
EXCEL_PATH = Path(__file__).parent / "Product Analytics Data (17th March).xlsx"
EXCEL_2026_PATH = Path(__file__).parent / "Product Analytics (16th April).xlsx"
ENTRIES_PATH = Path(__file__).parent / "Product Analytics Data Entries.xlsx"

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
FY_MONTH_ORDER = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
FY_MONTH_NAMES = [
    "Apr", "May", "Jun", "Jul", "Aug", "Sep",
    "Oct", "Nov", "Dec", "Jan", "Feb", "Mar",
]


def fy_label(year: int, month: int) -> str:
    """Return financial-year label (Apr-Mar), e.g. 'FY 2024-25'."""
    start = year if month >= 4 else year - 1
    return f"FY {start}-{str(start + 1)[-2:]}"


@st.cache_data
def load_data():
    """Load and merge audit-log data from both Excel files.

    The original file (17th March) covers historical data through early 2026.
    The newer file (16th April) has comprehensive Jan-Mar 2026 action data with
    explicit year/month columns that reflect when the action happened (the
    month_of_entry column in that file refers to the data period, not action
    date).  We drop partial 2026 rows from the old file and replace them with
    the complete new dataset.
    """
    # Historical data — derive year/month from month_of_entry
    df_old = pd.read_excel(EXCEL_PATH, sheet_name="data_audit_logs_v2")
    mo = pd.to_datetime(df_old["month_of_entry"])
    df_old["year"] = mo.dt.year
    df_old["month"] = mo.dt.month
    # Drop old (partial) 2026 rows — the new file supersedes them
    df_old = df_old[df_old["year"] < 2026]

    # New comprehensive 2026 Q1 data — year/month columns already present
    df_new = pd.read_excel(EXCEL_2026_PATH, sheet_name="data")

    # Align columns and merge
    shared_cols = [
        "user_name", "user_role", "company_name", "action", "message",
        "timestamp", "month_of_entry", "section", "business_unit_name",
        "my_metric_name", "month", "year",
    ]
    df = pd.concat([df_old[shared_cols], df_new[shared_cols]], ignore_index=True)

    df["action"] = df["action"].replace("deleted", "delete")
    df["fy_label"] = df.apply(lambda r: fy_label(int(r["year"]), int(r["month"])), axis=1)
    return df


@st.cache_data
def load_entries_data():
    """Load data entries Excel with caching."""
    df = pd.read_excel(ENTRIES_PATH, sheet_name="prodanalytics")
    df = df.rename(columns={
        "org_name": "company_name",
        "role_name": "user_role",
        "entry_month": "month",
        "entry_year": "year",
    })
    df = df[df["year"].isin([2024, 2025, 2026])]
    df["user_role"] = df["user_role"].fillna("Unknown")
    df["fy_label"] = df.apply(lambda r: fy_label(int(r["year"]), int(r["month"])), axis=1)
    return df


def apply_fy_filter(df: pd.DataFrame, fy: str) -> pd.DataFrame:
    """Filter dataframe by financial year label (Apr-Mar)."""
    if fy != "All":
        df = df[df["fy_label"] == fy]
    return df


# ── Notes helpers (Google Sheets backend) ──────────────────────────────────


def load_notes():
    """Load notes from Google Sheets, using session-state cache for speed.

    Returns None when Google Sheets is not configured.
    """
    if not GSHEETS_AVAILABLE:
        return None

    if "_notes" in st.session_state:
        return st.session_state["_notes"]

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Notes", ttl=30)
        if df is None:
            df = pd.DataFrame(columns=["id", "company", "title", "content", "created_at"])
        else:
            df = df.dropna(how="all")
        st.session_state["_notes"] = df
        return df
    except Exception:
        return None


def save_notes(df: pd.DataFrame) -> bool:
    """Write the full notes DataFrame to Google Sheets."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Notes", data=df)
        st.session_state["_notes"] = df
        return True
    except Exception:
        return False


# ── Main ───────────────────────────────────────────────────────────────────


def main():
    st.title("Product Analytics Dashboard")
    st.markdown("Module-wise and company-wise activity insights")

    # Load data (first load can take 1-2 min with large Excel files on cloud)
    with st.spinner("Loading data... Please wait 1-2 minutes on first visit."):
        df_raw = load_data()
        entries_raw = load_entries_data()

    # Shared FY filter (above tabs — applies to Overview & Module-wise Count)
    fy_options = sorted(set(
        df_raw["fy_label"].unique().tolist() + entries_raw["fy_label"].unique().tolist()
    ))
    selected_fy = st.selectbox(
        "Filter by financial year",
        ["All"] + fy_options,
        index=0,
    )
    df_year = apply_fy_filter(df_raw, selected_fy)
    df_entries = apply_fy_filter(entries_raw.copy(), selected_fy)

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_overview, tab_modules, tab_notes = st.tabs(
        ["Overview", "Module-wise Count", "Notes"]
    )

    # ── Tab 1: Overview ────────────────────────────────────────────────────
    with tab_overview:
        action_options = sorted(df_year["action"].dropna().unique().tolist())
        selected_actions = st.multiselect(
            "Filter by action type",
            options=action_options,
            default=action_options,
        )

        module_options = sorted(df_year["section"].dropna().unique().tolist())
        selected_modules = st.multiselect(
            "Filter by module",
            options=module_options,
            default=module_options,
        )

        df_actions = df_year[
            df_year["action"].isin(selected_actions) & df_year["section"].isin(selected_modules)
        ]
        st.caption("Action Type and Module filters apply only to action analytics.")

        # KPI cards
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Actions", f"{len(df_actions):,}")
        with col2:
            st.metric("Total Companies", df_actions["company_name"].nunique())
        with col3:
            st.metric("Total Modules", df_actions["section"].nunique())
        with col4:
            st.metric("Total User Roles", df_actions["user_role"].nunique())
        with col5:
            st.metric("Total Data Entries", f"{len(df_entries):,}")

        st.divider()

        # Company-wise horizontal bar chart (show all companies)
        st.subheader("Company-wise Activity")
        all_companies = sorted(
            df_raw[df_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
        )
        counted = df_actions.groupby("company_name").size().reindex(all_companies, fill_value=0)
        company_counts = counted.reset_index(name="action_count").sort_values(
            "action_count", ascending=True
        )

        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=company_counts["action_count"],
                    y=company_counts["company_name"],
                    orientation="h",
                    marker=dict(color="steelblue"),
                    text=company_counts["action_count"],
                    textposition="auto",
                )
            ]
        )
        fig_bar.update_layout(
            xaxis_title="Number of Actions",
            yaxis_title="Company",
            height=max(700, len(company_counts) * 32),
            margin=dict(l=180),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Action count trend: FY-wise (when All) or month-wise (when specific FY)
        trend_label = "FY-wise" if selected_fy == "All" else f"Month-wise ({selected_fy})"
        st.markdown(f"##### Action Count Over Time ({trend_label})")
        if selected_fy == "All":
            trend_data = df_actions.groupby("fy_label").size().reset_index(name="count")
            trend_data = trend_data.sort_values("fy_label")
            fig_trend = go.Figure(
                data=[
                    go.Scatter(
                        x=trend_data["fy_label"],
                        y=trend_data["count"],
                        mode="lines+markers+text",
                        line=dict(color="#2E86AB", width=3),
                        marker=dict(size=10),
                        text=trend_data["count"],
                        textposition="top center",
                    )
                ]
            )
            fig_trend.update_layout(
                xaxis=dict(
                    title="Financial Year",
                    type="category",
                    categoryorder="array",
                    categoryarray=sorted(df_raw["fy_label"].unique().tolist()),
                ),
                yaxis_title="Action Count",
                height=350,
                margin=dict(t=40),
            )
        else:
            month_counts = df_actions.groupby("month").size().reindex(FY_MONTH_ORDER, fill_value=0)
            trend_data = month_counts.reset_index()
            trend_data.columns = ["month", "count"]
            trend_data["month_label"] = [MONTH_NAMES[int(m) - 1] for m in trend_data["month"]]

            fig_trend = go.Figure(
                data=[
                    go.Scatter(
                        x=trend_data["month_label"],
                        y=trend_data["count"],
                        mode="lines+markers+text",
                        line=dict(color="#2E86AB", width=3),
                        marker=dict(size=10),
                        text=trend_data["count"],
                        textposition="top center",
                    )
                ]
            )
            fig_trend.update_layout(
                xaxis=dict(title="Month", type="category", categoryorder="array", categoryarray=FY_MONTH_NAMES),
                yaxis_title="Action Count",
                height=350,
                margin=dict(t=40),
            )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Company-wise Data Entries
        st.subheader("Company-wise Data Entries")
        all_companies_entries = sorted(
            entries_raw[entries_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
        )
        entries_counted = (
            df_entries.groupby("company_name")
            .size()
            .reindex(all_companies_entries, fill_value=0)
        )
        entries_company_counts = (
            entries_counted.reset_index(name="count")
            .sort_values("count", ascending=True)
        )
        fig_entries_bar = go.Figure(
            data=[
                go.Bar(
                    x=entries_company_counts["count"],
                    y=entries_company_counts["company_name"],
                    orientation="h",
                    marker=dict(color="#9B59B6"),
                    text=entries_company_counts["count"],
                    textposition="auto",
                )
            ]
        )
        fig_entries_bar.update_layout(
            xaxis_title="Number of Data Entries",
            yaxis_title="Company",
            height=max(500, len(entries_company_counts) * 32),
            margin=dict(l=180),
            showlegend=False,
        )
        st.plotly_chart(fig_entries_bar, use_container_width=True)

        # Data Entries Over Time
        entries_trend_label = "FY-wise" if selected_fy == "All" else f"Month-wise ({selected_fy})"
        st.markdown(f"##### Data Entries Over Time ({entries_trend_label})")
        if selected_fy == "All":
            entries_trend = (
                df_entries.groupby("fy_label")
                .size()
                .reset_index(name="count")
                .sort_values("fy_label")
            )
            fig_entries_trend = go.Figure(
                data=[
                    go.Scatter(
                        x=entries_trend["fy_label"],
                        y=entries_trend["count"],
                        mode="lines+markers+text",
                        line=dict(color="#9B59B6", width=3),
                        marker=dict(size=10),
                        text=entries_trend["count"],
                        textposition="top center",
                    )
                ]
            )
            fig_entries_trend.update_layout(
                xaxis=dict(
                    title="Financial Year",
                    type="category",
                    categoryorder="array",
                    categoryarray=sorted(entries_raw["fy_label"].unique().tolist()),
                ),
                yaxis_title="Data Entry Count",
                height=350,
                margin=dict(t=40),
            )
        else:
            entries_month = (
                df_entries.groupby("month")
                .size()
                .reindex(FY_MONTH_ORDER, fill_value=0)
            )
            entries_trend_data = entries_month.reset_index()
            entries_trend_data.columns = ["month", "count"]
            entries_trend_data["month_label"] = [
                MONTH_NAMES[int(m) - 1] for m in entries_trend_data["month"]
            ]
            fig_entries_trend = go.Figure(
                data=[
                    go.Scatter(
                        x=entries_trend_data["month_label"],
                        y=entries_trend_data["count"],
                        mode="lines+markers+text",
                        line=dict(color="#9B59B6", width=3),
                        marker=dict(size=10),
                        text=entries_trend_data["count"],
                        textposition="top center",
                    )
                ]
            )
            fig_entries_trend.update_layout(
                xaxis=dict(title="Month", type="category", categoryorder="array", categoryarray=FY_MONTH_NAMES),
                yaxis_title="Data Entry Count",
                height=350,
                margin=dict(t=40),
            )
        st.plotly_chart(fig_entries_trend, use_container_width=True)

        # Company selection for drill-down (union of actions and entries companies)
        actions_companies = df_raw[df_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
        entries_companies = entries_raw[entries_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
        company_list = sorted(list(set(actions_companies + entries_companies)))
        companies = ["-- Select a company --", "All"] + company_list
        selected_company = st.selectbox(
            "Select a company to view detailed insights",
            companies,
            key="company_select",
        )

        # Drill-down section
        if selected_company and selected_company != "-- Select a company --":
            st.divider()
            insight_label = "All Companies" if selected_company == "All" else selected_company
            st.subheader(f"Insights: {insight_label}")

            df_company = (
                df_actions
                if selected_company == "All"
                else df_actions[df_actions["company_name"] == selected_company]
            )

            section_colors = {
                "Data Manager": "#2E86AB",
                "User Management": "#A23B72",
                "Entity Manager": "#F18F01",
                "Supplier": "#C73E1D",
                "Reporting": "#3B1F2B",
                "Login with Google": "#95C623",
                "Materiality": "#6B5B95",
                "Targets": "#88B04B",
                "Utility Manager": "#DD4124",
            }
            role_colors = {
                "ADMIN": "#4A90D9",
                "CONTRIBUTOR": "#7B68EE",
                "DEPARTMENT_HEAD": "#50C878",
                "ESG_CONSULTANT": "#FFB347",
                "SUPER_ADMIN": "#E74C3C",
                "AUDITOR": "#9B59B6",
            }

            # Module Usage - full width
            st.markdown("##### Module Usage")
            section_counts = (
                df_company.groupby("section")
                .size()
                .sort_values(ascending=True)
                .reset_index(name="count")
            )
            fig_module = go.Figure(
                data=[
                    go.Bar(
                        x=section_counts["count"],
                        y=section_counts["section"],
                        orientation="h",
                        marker=dict(color="seagreen"),
                        text=section_counts["count"],
                        textposition="auto",
                    )
                ]
            )
            fig_module.update_layout(
                xaxis_title="Actions",
                height=350,
                margin=dict(l=120),
                showlegend=False,
            )
            st.plotly_chart(fig_module, use_container_width=True)

            # Action Breakdown (pie charts with % and count)
            st.markdown("##### Action Breakdown")
            st.caption("For each action, % and count by section (module)")
            action_section = (
                df_company.groupby(["action", "section"])
                .size()
                .reset_index(name="count")
            )
            pivot_action = action_section.pivot(
                index="action", columns="section", values="count"
            ).fillna(0)
            pivot_action["_total"] = pivot_action.sum(axis=1)
            pivot_action = pivot_action.sort_values("_total", ascending=False).drop(columns=["_total"])

            actions_list = pivot_action.index.tolist()
            n_cols = 3
            for i in range(0, len(actions_list), n_cols):
                cols = st.columns(n_cols)
                for j, col in enumerate(cols):
                    if i + j < len(actions_list):
                        action_name = actions_list[i + j]
                        row = pivot_action.loc[action_name]
                        labels = [s for s in row.index if row[s] > 0]
                        values = [int(row[s]) for s in labels]
                        colors = [section_colors.get(s, "#888") for s in labels]
                        with col:
                            fig_pie = go.Figure(
                                data=[
                                    go.Pie(
                                        labels=labels,
                                        values=values,
                                        hole=0.4,
                                        marker_colors=colors,
                                        textinfo="label+percent+value",
                                        textposition="auto",
                                        hovertemplate="%{label}<br>%{percent}<br>Count: %{value}<extra></extra>",
                                    )
                                ]
                            )
                            fig_pie.update_layout(
                                title=dict(text=action_name, font=dict(size=14)),
                                height=320,
                                margin=dict(t=50, b=20, l=20, r=20),
                                showlegend=False,
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)

            # User Role by Module (pie charts with % and count)
            st.markdown("##### User Role by Module")
            st.caption("For each module, % and count by user role")
            role_section = (
                df_company.groupby(["section", "user_role"])
                .size()
                .reset_index(name="count")
            )
            pivot = role_section.pivot(
                index="section", columns="user_role", values="count"
            ).fillna(0)
            pivot["_total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values("_total", ascending=False).drop(columns=["_total"])

            modules_list = pivot.index.tolist()
            n_cols = 3
            for i in range(0, len(modules_list), n_cols):
                cols = st.columns(n_cols)
                for j, col in enumerate(cols):
                    if i + j < len(modules_list):
                        module_name = modules_list[i + j]
                        row = pivot.loc[module_name]
                        labels = [r.replace("_", " ") for r in row.index if row[r] > 0]
                        values = [int(row[r]) for r in row.index if row[r] > 0]
                        colors = [role_colors.get(r, "#888") for r in row.index if row[r] > 0]
                        with col:
                            fig_pie = go.Figure(
                                data=[
                                    go.Pie(
                                        labels=labels,
                                        values=values,
                                        hole=0.4,
                                        marker_colors=colors,
                                        textinfo="label+percent+value",
                                        textposition="auto",
                                        hovertemplate="%{label}<br>%{percent}<br>Count: %{value}<extra></extra>",
                                    )
                                ]
                            )
                            fig_pie.update_layout(
                                title=dict(text=module_name, font=dict(size=14)),
                                height=320,
                                margin=dict(t=50, b=20, l=20, r=20),
                                showlegend=False,
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)

            # Data Entry Analytics (for selected company or All)
            st.divider()
            st.subheader("Data Entry Analytics")
            df_entries_company = (
                df_entries
                if selected_company == "All"
                else df_entries[df_entries["company_name"] == selected_company]
            )

            if len(df_entries_company) == 0:
                st.info(
                    f"No data entries found for **{insight_label}** in the selected period."
                )
            else:
                entries_view = st.selectbox(
                    "View by",
                    ["Total Over Time", "By User Role", "By Category"],
                    key="entries_view",
                )

                if entries_view == "Total Over Time":
                    if selected_fy == "All":
                        tot = (
                            df_entries_company.groupby("fy_label")
                            .size()
                            .reset_index(name="count")
                            .sort_values("fy_label")
                        )
                        fig_de = go.Figure(
                            data=[
                                go.Scatter(
                                    x=tot["fy_label"],
                                    y=tot["count"],
                                    mode="lines+markers+text",
                                    line=dict(color="#9B59B6", width=3),
                                    marker=dict(size=10),
                                    text=tot["count"],
                                    textposition="top center",
                                )
                            ]
                        )
                        fig_de.update_layout(
                            xaxis=dict(
                                title="Financial Year",
                                type="category",
                                categoryorder="array",
                                categoryarray=sorted(entries_raw["fy_label"].unique().tolist()),
                            ),
                            yaxis_title="Data Entries",
                            height=350,
                        )
                    else:
                        mon = (
                            df_entries_company.groupby("month")
                            .size()
                            .reindex(FY_MONTH_ORDER, fill_value=0)
                        )
                        mon_df = mon.reset_index()
                        mon_df.columns = ["month", "count"]
                        mon_df["month_label"] = [MONTH_NAMES[int(m) - 1] for m in mon_df["month"]]
                        fig_de = go.Figure(
                            data=[
                                go.Scatter(
                                    x=mon_df["month_label"],
                                    y=mon_df["count"],
                                    mode="lines+markers+text",
                                    line=dict(color="#9B59B6", width=3),
                                    marker=dict(size=10),
                                    text=mon_df["count"],
                                    textposition="top center",
                                )
                            ]
                        )
                        fig_de.update_layout(
                            xaxis=dict(title="Month", type="category", categoryorder="array", categoryarray=FY_MONTH_NAMES),
                            yaxis_title="Data Entries",
                            height=350,
                        )
                    st.plotly_chart(fig_de, use_container_width=True)

                elif entries_view == "By User Role":
                    if selected_fy == "All":
                        role_yr = (
                            df_entries_company.groupby(["fy_label", "user_role"])
                            .size()
                            .unstack(fill_value=0)
                        )
                        role_yr = role_yr.sort_index()
                        fig_de = go.Figure()
                        for col in role_yr.columns:
                            fig_de.add_trace(
                                go.Scatter(
                                    x=role_yr.index,
                                    y=role_yr[col],
                                    name=col.replace("_", " "),
                                    mode="lines+markers",
                                )
                            )
                        fig_de.update_layout(
                            xaxis=dict(
                                title="Financial Year",
                                type="category",
                                categoryorder="array",
                                categoryarray=sorted(entries_raw["fy_label"].unique().tolist()),
                            ),
                            yaxis_title="Data Entries",
                            height=350,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        )
                    else:
                        role_mo = (
                            df_entries_company.groupby(["month", "user_role"])
                            .size()
                            .unstack(fill_value=0)
                        )
                        role_mo = role_mo.reindex(FY_MONTH_ORDER, fill_value=0)
                        role_mo.index = [MONTH_NAMES[i - 1] for i in role_mo.index]
                        fig_de = go.Figure()
                        for col in role_mo.columns:
                            fig_de.add_trace(
                                go.Scatter(
                                    x=role_mo.index,
                                    y=role_mo[col],
                                    name=col.replace("_", " "),
                                    mode="lines+markers",
                                )
                            )
                        fig_de.update_layout(
                            xaxis=dict(title="Month", type="category", categoryorder="array", categoryarray=FY_MONTH_NAMES),
                            yaxis_title="Data Entries",
                            height=350,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        )
                    st.plotly_chart(fig_de, use_container_width=True)

                else:  # By Category
                    colors = px.colors.qualitative.Set2
                    if selected_fy == "All":
                        cat_yr = (
                            df_entries_company.groupby(["fy_label", "metric_category"])
                            .size()
                            .unstack(fill_value=0)
                        )
                        cat_yr = cat_yr.sort_index()
                        fig_de = go.Figure()
                        colors = px.colors.qualitative.Set2
                        for i, col in enumerate(cat_yr.columns):
                            fig_de.add_trace(
                                go.Scatter(
                                    x=cat_yr.index,
                                    y=cat_yr[col],
                                    name=col[:40] + ("..." if len(str(col)) > 40 else ""),
                                    mode="lines+markers",
                                    line=dict(color=colors[i % len(colors)]),
                                )
                            )
                        fig_de.update_layout(
                            xaxis=dict(
                                title="Financial Year",
                                type="category",
                                categoryorder="array",
                                categoryarray=sorted(entries_raw["fy_label"].unique().tolist()),
                            ),
                            yaxis_title="Data Entries",
                            height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=9)),
                        )
                    else:
                        cat_mo = (
                            df_entries_company.groupby(["month", "metric_category"])
                            .size()
                            .unstack(fill_value=0)
                        )
                        cat_mo = cat_mo.reindex(FY_MONTH_ORDER, fill_value=0)
                        cat_mo.index = [MONTH_NAMES[i - 1] for i in cat_mo.index]
                        fig_de = go.Figure()
                        for i, col in enumerate(cat_mo.columns):
                            fig_de.add_trace(
                                go.Scatter(
                                    x=cat_mo.index,
                                    y=cat_mo[col],
                                    name=col[:40] + ("..." if len(str(col)) > 40 else ""),
                                    mode="lines+markers",
                                    line=dict(color=colors[i % len(colors)]),
                                )
                            )
                        fig_de.update_layout(
                            xaxis=dict(title="Month", type="category", categoryorder="array", categoryarray=FY_MONTH_NAMES),
                            yaxis_title="Data Entries",
                            height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=9)),
                        )
                    st.plotly_chart(fig_de, use_container_width=True)

    # ── Tab 2: Module-wise Count ───────────────────────────────────────────
    with tab_modules:
        st.subheader("Module-wise Action Count")
        module_counts = (
            df_year.groupby("section")
            .size()
            .sort_values(ascending=True)
            .reset_index(name="count")
        )
        fig_mod = go.Figure(
            data=[
                go.Bar(
                    x=module_counts["count"],
                    y=module_counts["section"],
                    orientation="h",
                    marker=dict(color="seagreen"),
                    text=module_counts["count"],
                    textposition="auto",
                )
            ]
        )
        fig_mod.update_layout(
            xaxis_title="Action Count",
            yaxis_title="Module",
            height=max(400, len(module_counts) * 45),
            margin=dict(l=160),
            showlegend=False,
        )
        st.plotly_chart(fig_mod, use_container_width=True)

    # ── Tab 3: Notes ───────────────────────────────────────────────────────
    with tab_notes:
        st.subheader("Client Notes")

        notes_df = load_notes()

        if notes_df is None:
            st.warning("**Google Sheets connection not configured.**")
            st.markdown(
                """
To enable the Notes tab, connect a Google Sheet:

1. **Google Cloud Console** — create a project (free) and enable the
   **Google Sheets API**.
2. **Service account** — create one and download the JSON key file.
3. **Google Sheet** — create a new spreadsheet, add a worksheet called
   `Notes` with these column headers in row 1:

   `id` | `company` | `title` | `content` | `created_at`

4. **Share** the sheet with the service account e-mail (Editor access).
5. **Streamlit secrets** — add credentials to `.streamlit/secrets.toml`
   (locally) or the Streamlit Cloud secrets panel:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID"
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```
"""
            )
        else:
            # Build the company list for the Add Note form
            actions_co = df_raw[df_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
            entries_co = entries_raw[entries_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
            notes_co = notes_df["company"].dropna().unique().tolist() if len(notes_df) > 0 else []
            all_note_companies = sorted(set(actions_co + entries_co + notes_co))

            # ── Add Note form ──────────────────────────────────────────────
            with st.form("add_note", clear_on_submit=True):
                st.markdown("##### Add New Note")
                note_company = st.selectbox("Company", all_note_companies, key="note_company")
                note_title = st.text_input("Title")
                note_content = st.text_area("Content", height=150)
                submitted = st.form_submit_button("Save Note", type="primary")

                if submitted:
                    if not note_title.strip() or not note_content.strip():
                        st.error("Title and content are required.")
                    else:
                        new_row = pd.DataFrame([{
                            "id": str(uuid.uuid4()),
                            "company": note_company,
                            "title": note_title.strip(),
                            "content": note_content.strip(),
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        }])
                        updated = pd.concat([notes_df, new_row], ignore_index=True)
                        if save_notes(updated):
                            st.success("Note saved!")
                            st.rerun()
                        else:
                            st.error("Failed to save note. Check your Google Sheets connection.")

            st.divider()

            # ── Search & Filter ────────────────────────────────────────────
            filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 1])
            with filter_col1:
                search_query = st.text_input(
                    "Search notes",
                    placeholder="Search by title or content...",
                )
            with filter_col2:
                if len(notes_df) > 0:
                    note_company_options = ["All"] + sorted(notes_df["company"].dropna().unique().tolist())
                else:
                    note_company_options = ["All"]
                filter_company = st.selectbox(
                    "Filter by company",
                    note_company_options,
                    key="notes_company_filter",
                )
            with filter_col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Refresh", key="refresh_notes"):
                    st.session_state.pop("_notes", None)
                    st.rerun()

            # Apply filters
            filtered = notes_df.copy()
            if filter_company != "All":
                filtered = filtered[filtered["company"] == filter_company]
            if search_query:
                mask = (
                    filtered["title"].str.contains(search_query, case=False, na=False)
                    | filtered["content"].str.contains(search_query, case=False, na=False)
                )
                filtered = filtered[mask]

            if "created_at" in filtered.columns and not filtered.empty:
                filtered = filtered.sort_values("created_at", ascending=False)

            # ── Display notes ──────────────────────────────────────────────
            st.markdown(f"**{len(filtered)} note(s)**")
            if filtered.empty:
                st.info("No notes found. Add one using the form above.")
            else:
                for _, note in filtered.iterrows():
                    header = f"**{note['title']}** — {note['company']}  \u00a0\u00a0\u00a0 _{note.get('created_at', '')}_"
                    with st.expander(header):
                        st.write(note["content"])
                        if st.button("Delete this note", key=f"del_{note['id']}", type="secondary"):
                            updated = notes_df[notes_df["id"] != note["id"]]
                            if save_notes(updated):
                                st.success("Note deleted.")
                                st.rerun()
                            else:
                                st.error("Failed to delete note.")


if __name__ == "__main__":
    main()
