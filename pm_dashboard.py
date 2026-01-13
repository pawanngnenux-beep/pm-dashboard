import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="PM Dashboard",
    layout="wide"
)

st.title("📊 Project Management Dashboard")

# -------------------------------------------------
# Load Data
# -------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("dataa.xlsx")
    df.columns = df.columns.str.strip()

    # Date handling
    if 'Assinged Date' in df.columns:
        df['Assinged Date'] = pd.to_datetime(df['Assinged Date'], errors='coerce')
    if 'Completed Date' in df.columns:
        df['Completed Date'] = pd.to_datetime(df['Completed Date'], errors='coerce')

    return df

df = load_data()

# -------------------------------------------------
# Sidebar Filters
# -------------------------------------------------
st.sidebar.header("🔎 Filters")

status_options = df['Status'].dropna().unique().tolist()
owner_options = df['assigned'].dropna().unique().tolist()

selected_status = st.sidebar.multiselect(
    "Status",
    options=status_options,
    default=status_options
)

selected_owner = st.sidebar.multiselect(
    "Owner",
    options=owner_options,
    default=owner_options
)

filtered_df = df[
    (df['Status'].isin(selected_status)) &
    (df['assigned'].isin(selected_owner))
]

# -------------------------------------------------
# KPI Metrics
# -------------------------------------------------
completed_tasks = filtered_df['Completed Date'].notna().sum()
pending_tasks = filtered_df['Completed Date'].isna().sum()
validated_tasks = (filtered_df['Validate (Y/N)'] == 'Y').sum()

col1, col2, col3 = st.columns(3)
col1.metric("✅ Completed Tasks", completed_tasks)
col2.metric("⏳ Pending Tasks", pending_tasks)
col3.metric("✔ Validated Tasks", validated_tasks)

st.divider()

# -------------------------------------------------
# Tasks by Status
# -------------------------------------------------
st.subheader("📌 Tasks by Status")

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

# -------------------------------------------------
# Tasks by Owner
# -------------------------------------------------
st.subheader("👤 Tasks by Owner")

owner_summary = (
    filtered_df.groupby('assigned')
    .size()
    .reset_index(name='Task Count')
)

fig, ax = plt.subplots()
ax.bar(owner_summary['assigned'], owner_summary['Task Count'])
ax.set_xlabel("Owner")
ax.set_ylabel("Task Count")
plt.xticks(rotation=45)
st.pyplot(fig)

# -------------------------------------------------
# Validation Status
# -------------------------------------------------
st.subheader("🧪 Validation Status")

validation_summary = (
    filtered_df.groupby('Validate (Y/N)')
    .size()
    .reset_index(name='Task Count')
)

fig, ax = plt.subplots()
ax.pie(
    validation_summary['Task Count'],
    labels=validation_summary['Validate (Y/N)'],
    autopct='%1.1f%%'
)
st.pyplot(fig)

# -------------------------------------------------
# Overdue Tasks
# -------------------------------------------------
st.subheader("🚨 Overdue Tasks")

today = pd.Timestamp.today()
overdue_tasks = filtered_df[
    (filtered_df['Completed Date'].isna()) &
    (filtered_df['Assinged Date'].notna()) &
    ((today - filtered_df['Assinged Date']).dt.days > 14)
]

st.dataframe(
    overdue_tasks[['Name', 'Status', 'assigned', 'Assinged Date']],
    use_container_width=True
)

# -------------------------------------------------
# Task Tracker Table
# -------------------------------------------------
st.subheader("📋 Task Tracker")

st.dataframe(
    filtered_df[
        ['Name', 'Status', 'assigned', 'Validate (Y/N)',
         'Result', 'Assinged Date', 'Completed Date']
    ],
    use_container_width=True
)
