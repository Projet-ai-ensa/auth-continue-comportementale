import plotly.express as px
import streamlit as st

from dashboard.metrics import average_by_label, filter_windows, summarize
from data.reader import FEATURE_COLUMNS, read_features

# Same colours everywhere: red = bot, blue = human
COLORS = {"bot": "#e4572e", "human": "#2e86de"}

st.set_page_config(page_title="Bot Detection Dashboard", layout="wide")

st.title("Bot Detection Dashboard")
st.caption("Data: data/synthetic_features.csv (synthetic, for development)")

# Load Saad's CSV with Saad's own reader (it checks the columns)
df = read_features("data/synthetic_features.csv")

# --- Filters (left sidebar) ---
st.sidebar.header("Filters")
all_labels = sorted(df["label"].unique())
labels = st.sidebar.multiselect("Label", options=all_labels, default=all_labels)

all_bot_types = sorted(df["bot_config"].dropna().unique())
bot_types = st.sidebar.multiselect("Bot type", options=all_bot_types, default=all_bot_types)

df = filter_windows(df, labels, bot_types)

if df.empty:
    st.warning("No data for these filters.")
    st.stop()

# --- Key numbers ---
summary = summarize(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Windows", summary["windows"])
col2.metric("Sessions", summary["sessions"])
col3.metric("Participants", summary["participants"])
col4.metric("Bot windows", f"{summary['bot_share']:.0f} %")

# --- Humans vs bots: average of each measurement ---
st.subheader("Average per label")
feature = st.selectbox("Measurement", FEATURE_COLUMNS, index=1)
averages = average_by_label(df, feature)
fig = px.bar(averages, x="label", y=feature, color="label", color_discrete_map=COLORS)
st.plotly_chart(fig, width="stretch")

# --- Speed vs how much it varies ---
st.subheader("Mouse speed vs speed variation")
st.caption("Humans: medium speed, lots of variation. Simple bots: fast and very regular.")
fig = px.scatter(
    df,
    x="mouse_speed_mean_px_s",
    y="mouse_speed_std_px_s",
    color="label",
    color_discrete_map=COLORS,
    hover_data=["participant_id", "session_id", "bot_config"],
)
st.plotly_chart(fig, width="stretch")

# --- Table ---
st.subheader("All observation windows")
st.dataframe(df, hide_index=True)