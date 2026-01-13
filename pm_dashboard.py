import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# =================================================
# Page Config
# =================================================
st.set_page_config(
    page_title="PM Executive Dashboard",
    layout="wide"
)

st.title("📊 Project Management Executive Dashboard")

# =================================================
# Load Data
# =================================================
@st.cache_data
def load_data():
    df = pd.read_excel("dataa.xlsx")
    df.columns = df.columns.str.strip()

    if 'Assinged Date' in df.columns:
        df['Assinged Date'] = pd.to_datetime(df['Assinged Date'], errors='coerce')
    if 'Completed Date' in df.columns:
        df['Completed Date'] = pd.to_datetime(df['Completed Date'], errors='coerce')

    return df

df = load_data()

# =================================================
# Sidebar Filters
# =================================================
st.sidebar.header("🔎 Filters")

status_filter = st.sidebar.multiselect(
    "Status",
    options=df['Status'].dropna().unique(),
    default=df['Status'].dropna().unique()
)

owner_filter = st.sidebar.multiselect(
    "Owner",
    options=df['assigned'].dropna().unique(),
    default=df['assigned'].dropna().unique()
)

filtered_df = df[
    (df['Status'].isin(status_filter)) &
    (df['assigned'].isin(owner_filter))
]

# =================================================
# Download Helper
# =================================================
def download_excel(dataframe, filename):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, index=False)
    st.download_button(
        label="⬇ Download Excel",
        data=buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =================================================
# KPI Section (Executive First View)
# =================================================
completed = (filtered_df['Status'].str.lower() == 'done').sum()
pending = (filtered_df['Status'].str.lower() != 'done').sum()
validated = (filtered_df['Validate (Y/N)'] == 'Y').sum()

k1, k2, k3 = st.columns(3)
k1.metric("✅ Completed Tasks", completed)
k2.metric("⏳ Pending Tasks", pending)
k3.metric("✔ Validated Tasks", validated)

st.divider()

# =================================================
# TABS
# =================================================
tab_overview, tab_delivery, tab_risk = st.tabs(
    ["📌 Overview", "🚚 Delivery", "⚠ Risk"]
)

# =================================================
# OVERVIEW TAB
# =================================================
with tab_overview:
    st.subheader("Tasks by Status")

    status_summary = (
        filtered_df.groupby('Status')
        .size()
        .reset_index(name='Task Count')
    )

    fig, ax = plt.subplots()
    ax.bar(status_summary['Status'], status_summary['Task Count'])
    ax.set_xlabel("Status")
    ax.set_ylabel("Task Count")
    st.pyplot(fig)

    download_excel(status_summary, "status_summary.xlsx")

    st.subheader("Owner Workload")

    owner_summary = (
        filtered_df.groupby('assigned')
        .size()
        .reset_index(name='Task Count')
    )

    fig, ax = plt.subplots()
    ax.bar(owner_summary['assigned'], owner_summary['Task Count'])
    plt.xticks(rotation=45)
    st.pyplot(fig)

    download_excel(owner_summary, "owner_workload.xlsx")

    st.subheader("Status × Owner Matrix")

    status_owner_matrix = pd.pivot_table(
        filtered_df,
        index='assigned',
        columns='Status',
        values='Name',
        aggfunc='count',
        fill_value=0
    )

    st.dataframe(status_owner_matrix, use_container_width=True)
    download_excel(status_owner_matrix.reset_index(), "status_owner_matrix.xlsx")

# =================================================
# DELIVERY TAB
# =================================================
with tab_delivery:
    st.subheader("Completion Overview")

    completion_table = pd.DataFrame({
        "Completed": [completed],
        "Pending": [pending]
    })

    st.dataframe(completion_table)
    download_excel(completion_table, "completion_overview.xlsx")

    st.subheader("Cycle Time (Days)")

    cycle_df = filtered_df[
    filtered_df['Status'].str.lower() == 'done'
].copy()

cycle_df['Cycle Time (Days)'] = (
    cycle_df['Completed Date'] - cycle_df['Assinged Date']
).dt.days


     st.subheader("Cycle Time (Days)")

    cycle_df = filtered_df[
        filtered_df['Status'].str.lower() == 'done'
    ].copy()

    cycle_df['Cycle Time (Days)'] = (
        cycle_df['Completed Date'] - cycle_df['Assinged Date']
    ).dt.days

    cycle_table = cycle_df[
        cycle_df['Cycle Time (Days)'].notna()
    ][
        ['Name', 'assigned', 'Status', 'Cycle Time (Days)']
    ].sort_values('Cycle Time (Days)', ascending=False)

    st.dataframe(cycle_table, use_container_width=True)
    download_excel(cycle_table, "cycle_time.xlsx")


    st.subheader("Monthly Completion Trend")

    monthly = filtered_df[
    filtered_df['Status'].str.lower() == 'done'
].copy()

    monthly['Month'] = monthly['Completed Date'].dt.to_period('M').astype(str)

    monthly_summary = (
        monthly.groupby('Month')
        .size()
        .reset_index(name='Completed Tasks')
        .sort_values('Month')
    )

    st.dataframe(monthly_summary, use_container_width=True)
    download_excel(monthly_summary, "monthly_completion.xlsx")

# =================================================
# RISK TAB
# =================================================
with tab_risk:
    st.subheader("Overdue Tasks")

    today = pd.Timestamp.today()

    overdue_tasks = filtered_df[
    (filtered_df['Status'].str.lower() != 'done') &
    (filtered_df['Assinged Date'].notna()) &
    ((today - filtered_df['Assinged Date']).dt.days > 14)
][
        ['Name', 'Status', 'assigned', 'Assinged Date']
    ]

    if overdue_tasks.empty:
        st.success("No overdue tasks 🎉")
    else:
        st.dataframe(overdue_tasks, use_container_width=True)
        download_excel(overdue_tasks, "overdue_tasks.xlsx")

    st.subheader("Validation Pending")

    pending_validation = filtered_df[
        filtered_df['Validate (Y/N)'] != 'Y'
    ][
        ['Name', 'Status', 'assigned', 'Completed Date']
    ]

    if pending_validation.empty:
        st.success("All tasks validated ✔")
    else:
        st.dataframe(pending_validation, use_container_width=True)
        download_excel(pending_validation, "pending_validation.xlsx")

    st.subheader("Risk / Failed Tasks")

    risk_tasks = filtered_df[
        filtered_df['Result'].str.contains(
            'fail|block|risk|issue',
            case=False,
            na=False
        )
    ][
        ['Name', 'Status', 'assigned', 'Result', 'Notes']
    ]

    if risk_tasks.empty:
        st.info("No risk indicators found.")
    else:
        st.dataframe(risk_tasks, use_container_width=True)
        download_excel(risk_tasks, "risk_tasks.xlsx")

# =================================================
# MASTER TASK TRACKER (BOTTOM)
# =================================================
st.divider()
st.subheader("📋 Master Task Tracker")

st.dataframe(
    filtered_df[
        ['Name', 'Status', 'assigned', 'Validate (Y/N)',
         'Result', 'Assinged Date', 'Completed Date']
    ],
    use_container_width=True
)

download_excel(filtered_df, "full_task_tracker.xlsx")


