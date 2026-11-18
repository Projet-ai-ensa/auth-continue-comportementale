import streamlit as st

from data.reader import FEATURE_COLUMNS, read_features

st.set_page_config(page_title="Bot Detection Dashboard", layout="wide")

st.title("Bot Detection Dashboard")
st.caption("Data: data/synthetic_features.csv (synthetic, for development)")

# Load Saad's CSV with Saad's own reader (it checks the columns)
df = read_features("data/synthetic_features.csv")

# --- Filters (left sidebar) ---
st.sidebar.header("Filters")
labels = st.sidebar.multiselect(
    "Label", options=sorted(df["label"].unique()), default=sorted(df["label"].unique())
)
df = df[df["label"].isin(labels)]

if df.empty:
    st.warning("No data for these filters.")
    st.stop()

# --- Key numbers ---
n_windows = len(df)
n_sessions = df["session_id"].nunique()
n_participants = df["participant_id"].nunique()
bot_share = (df["label"] == "bot").mean() * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Windows", n_windows)
col2.metric("Sessions", n_sessions)
col3.metric("Participants", n_participants)
col4.metric("Bot windows", f"{bot_share:.0f} %")

# --- Humans vs bots: average of each measurement ---
st.subheader("Average per label")
feature = st.selectbox("Measurement", FEATURE_COLUMNS, index=1)
averages = df.groupby("label")[feature].mean().reset_index()
st.bar_chart(averages, x="label", y=feature)

# --- Speed vs how much it varies ---
st.subheader("Mouse speed vs speed variation")
st.caption("Humans: medium speed, lots of variation. Simple bots: fast and very regular.")
st.scatter_chart(
    df,
    x="mouse_speed_mean_px_s",
    y="mouse_speed_std_px_s",
    color="label",
)

# --- Table ---
st.subheader("All observation windows")
st.dataframe(df, hide_index=True)