import streamlit as st
import pandas as pd
from firebase_config import db
from datetime import date

st.set_page_config(page_title="Ripples in Motion Activity Tracker", layout="wide")

st.title("🏃‍♂️ Ripples in Motion - Activity Tracker")

# --- Input Form ---
st.header("Add Your Daily Activity")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    member_name = st.text_input("👤 Member Name")
with col2:
    activity = st.selectbox(
        "🏋️ Activity",
        ["Walking", "Running", "Cycling", "Yoga", "Gym", "Badminton", "Dance", "Trekking", "Volley Ball"]
    )
with col3:
    distance = st.number_input("📏 Distance (km)", min_value=0.0, step=0.1)
with col4:
    duration = st.number_input("⏱ Duration (minutes)", min_value=0.0, step=1.0)
with col5:
    activity_date = st.date_input("📅 Date", date.today())

if st.button("Submit Activity"):
    if member_name:
        doc_ref = db.collection("activities").document()
        doc_ref.set({
            "member_name": member_name,
            "activity": activity,
            "distance": distance,
            "duration": duration,
            "date": activity_date.isoformat()
        })
        st.success("✅ Activity added successfully!")
    else:
        st.warning("Please enter a member name!")

# --- Fetch and Display Data ---
st.header("📊 Activity Dashboard")

docs = db.collection("activities").stream()
data = [doc.to_dict() for doc in docs]

if len(data) > 0:
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    # Calculate Points (same as your Google Sheet logic)
    def calculate_points(row):
        act, dist, dur = row["activity"], row["distance"], row["duration"]
        if act == "Walking": return (dist * 8) + ((dist / dur) * 10) if dur else dist * 8
        if act == "Running": return (dist * 18) + ((dist / dur) * 25) if dur else dist * 18
        if act == "Cycling": return (dist * 10) + ((dist / dur) * 15) if dur else dist * 10
        if act == "Yoga": return dur * 0.5
        if act == "Gym": return dur * 1.75
        if act == "Badminton": return dur * 1.25
        if act == "Dance": return dur * 1
        if act == "Trekking": return dur * 1.25
        if act == "Volley Ball": return dur * 0.8
        return dur
    df["Points"] = df.apply(calculate_points, axis=1)

    # Show full table
    st.dataframe(df.sort_values(by="date", ascending=False), use_container_width=True)

    # Leaderboard
    st.subheader("🏅 Leaderboard (Top Performers)")
    leaderboard = df.groupby("member_name")["Points"].sum().reset_index().sort_values("Points", ascending=False)
    st.dataframe(leaderboard, use_container_width=True)
else:
    st.info("No activity records found yet.")
