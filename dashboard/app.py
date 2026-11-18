import streamlit as st

from data.reader import read_features

st.title("Bot Detection Dashboard")
st.caption("Data: data/synthetic_features.csv (synthetic, for development)")

# Load Saad's CSV with Saad's own reader (it checks the columns)
df = read_features("data/synthetic_features.csv")

st.subheader("All observation windows")
st.dataframe(df)