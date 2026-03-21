"""
Product Analytics Dashboard
Module-wise and company-wise activity insights with year filtering.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page config
st.set_page_config(page_title="Product Analytics Dashboard", page_icon="📊", layout="wide")

# Path to Excel files (same directory as app)
EXCEL_PATH = Path(__file__).parent / "Product Analytics Data (17th March).xlsx"
ENTRIES_PATH = Path(__file__).parent / "Product Analytics Data Entries.xlsx"

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


@st.cache_data
def load_data():
    """Load and preprocess Excel data with caching."""
    df = pd.read_excel(EXCEL_PATH, sheet_name="data_audit_logs_v2")
    mo = pd.to_datetime(df["month_of_entry"])
    df["year"] = mo.dt.year
    df["month"] = mo.dt.month
    # Combine "delete" and "deleted" as same action
    df["action"] = df["action"].replace("deleted", "delete")
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
    return df


def apply_year_filter(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """Filter dataframe to 2024-2026 and optionally by specific year."""
    df = df[df["year"].isin([2024, 2025, 2026])]
    if year != "All":
        df = df[df["year"] == int(year)]
    return df


def main():
    st.title("Product Analytics Dashboard")
    st.markdown("Module-wise and company-wise activity insights")

    # Load data
    df_raw = load_data()
    entries_raw = load_entries_data()

    # Year filter
    year = st.selectbox(
        "Filter by year",
        ["All", "2024", "2025", "2026"],
        index=0,
    )
    df = apply_year_filter(df_raw, year)
    df_entries = apply_year_filter(entries_raw.copy(), year)

    # KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Actions", f"{len(df):,}")
    with col2:
        st.metric("Total Companies", df["company_name"].nunique())
    with col3:
        st.metric("Total Modules", df["section"].nunique())
    with col4:
        st.metric("Total User Roles", df["user_role"].nunique())
    with col5:
        st.metric("Total Data Entries", f"{len(df_entries):,}")

    st.divider()

    # Company-wise horizontal bar chart (show all companies)
    st.subheader("Company-wise Activity")
    all_companies = sorted(
        df_raw[df_raw["year"].isin([2024, 2025, 2026])]["company_name"].unique().tolist()
    )
    counted = df.groupby("company_name").size().reindex(all_companies, fill_value=0)
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

    # Action count trend: year-wise (when All) or month-wise (when specific year)
    trend_label = "Year-wise" if year == "All" else f"Month-wise ({year})"
    st.markdown(f"##### Action Count Over Time ({trend_label})")
    if year == "All":
        trend_data = df.groupby("year").size().reset_index(name="count")
        trend_data = trend_data.sort_values("year")
        fig_trend = go.Figure(
            data=[
                go.Scatter(
                    x=trend_data["year"].astype(str),
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
            xaxis_title="Year",
            yaxis_title="Action Count",
            height=350,
            margin=dict(t=40),
        )
    else:
        month_counts = df.groupby("month").size().reindex(range(1, 13), fill_value=0)
        trend_data = month_counts.reset_index()
        trend_data.columns = ["month", "count"]
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        trend_data["month_label"] = [month_names[int(m) - 1] for m in trend_data["month"]]

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
            xaxis_title="Month",
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
    entries_trend_label = "Year-wise" if year == "All" else f"Month-wise ({year})"
    st.markdown(f"##### Data Entries Over Time ({entries_trend_label})")
    if year == "All":
        entries_trend = (
            df_entries.groupby("year")
            .size()
            .reset_index(name="count")
            .sort_values("year")
        )
        fig_entries_trend = go.Figure(
            data=[
                go.Scatter(
                    x=entries_trend["year"].astype(str),
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
            xaxis_title="Year",
            yaxis_title="Data Entry Count",
            height=350,
            margin=dict(t=40),
        )
    else:
        entries_month = (
            df_entries.groupby("month")
            .size()
            .reindex(range(1, 13), fill_value=0)
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
            xaxis_title="Month",
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

        df_company = df if selected_company == "All" else df[df["company_name"] == selected_company]

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
                if year == "All":
                    tot = (
                        df_entries_company.groupby("year")
                        .size()
                        .reset_index(name="count")
                        .sort_values("year")
                    )
                    fig_de = go.Figure(
                        data=[
                            go.Scatter(
                                x=tot["year"].astype(str),
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
                        xaxis_title="Year",
                        yaxis_title="Data Entries",
                        height=350,
                    )
                else:
                    mon = (
                        df_entries_company.groupby("month")
                        .size()
                        .reindex(range(1, 13), fill_value=0)
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
                        xaxis_title="Month",
                        yaxis_title="Data Entries",
                        height=350,
                    )
                st.plotly_chart(fig_de, use_container_width=True)

            elif entries_view == "By User Role":
                if year == "All":
                    role_yr = (
                        df_entries_company.groupby(["year", "user_role"])
                        .size()
                        .unstack(fill_value=0)
                    )
                    fig_de = go.Figure()
                    for col in role_yr.columns:
                        fig_de.add_trace(
                            go.Scatter(
                                x=role_yr.index.astype(str),
                                y=role_yr[col],
                                name=col.replace("_", " "),
                                mode="lines+markers",
                            )
                        )
                    fig_de.update_layout(
                        xaxis_title="Year",
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
                    role_mo = role_mo.reindex(range(1, 13), fill_value=0)
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
                        xaxis_title="Month",
                        yaxis_title="Data Entries",
                        height=350,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    )
                st.plotly_chart(fig_de, use_container_width=True)

            else:  # By Category
                colors = px.colors.qualitative.Set2
                if year == "All":
                    cat_yr = (
                        df_entries_company.groupby(["year", "metric_category"])
                        .size()
                        .unstack(fill_value=0)
                    )
                    fig_de = go.Figure()
                    colors = px.colors.qualitative.Set2
                    for i, col in enumerate(cat_yr.columns):
                        fig_de.add_trace(
                            go.Scatter(
                                x=cat_yr.index.astype(str),
                                y=cat_yr[col],
                                name=col[:40] + ("..." if len(str(col)) > 40 else ""),
                                mode="lines+markers",
                                line=dict(color=colors[i % len(colors)]),
                            )
                        )
                    fig_de.update_layout(
                        xaxis_title="Year",
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
                    cat_mo = cat_mo.reindex(range(1, 13), fill_value=0)
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
                        xaxis_title="Month",
                        yaxis_title="Data Entries",
                        height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=9)),
                    )
                st.plotly_chart(fig_de, use_container_width=True)


if __name__ == "__main__":
    main()
