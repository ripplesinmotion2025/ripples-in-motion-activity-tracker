import streamlit as st
from firebase_config import db
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(page_title="Ripples In Motion Tracker", layout="wide")

# --- USER REGISTRATION ---
def register_user():
    st.header("🏃‍♀️ Register New User")

    name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth", min_value=datetime.date(1950, 1, 1))
    phone = st.text_input("Phone / WhatsApp Number")
    height = st.number_input("Height (cm, optional)", min_value=0, step=1)
    weight = st.number_input("Weight (kg, optional)", min_value=0, step=1)

    if st.button("Register"):
        if name and phone:
            db.collection("users").document(phone).set({
                "name": name,
                "dob": dob.isoformat(),
                "phone": phone,
                "height": height,
                "weight": weight,
                "createdAt": datetime.datetime.now().isoformat()
            })
            st.success("✅ Registration successful! You can now log your activities.")
            st.session_state["user"] = phone
            st.rerun()
        else:
            st.warning("⚠️ Please fill in at least your name and phone number.")


# --- LOGIN OR REGISTER ---
def login_page():
    st.title("🏋️ Ripples In Motion Tracker")

    if "user" not in st.session_state:
        st.session_state["user"] = None

    if st.session_state["user"]:
        show_dashboard()
        return

    phone = st.text_input("Enter your registered phone number to continue")
    if st.button("Continue"):
        user_ref = db.collection("users").document(phone).get()
        if user_ref.exists:
            st.session_state["user"] = phone
            st.success(f"Welcome back, {user_ref.to_dict()['name']}!")
            st.rerun()
        else:
            st.info("New user detected. Please register below 👇")
            register_user()


# --- ACTIVITY LOGGING ---
def log_activity(user):
    st.subheader("📝 Log Your Activity")
    activity = st.selectbox("Select Activity", [
        "Walking", "Jogging", "Running", "Cycling",
        "Trekking", "Badminton", "Pickle Ball", "Volley Ball",
        "Gym", "Yoga", "Dance"
    ])
    duration = st.number_input("Duration (minutes)", min_value=0)
    distance = st.number_input("Distance (km, optional)", min_value=0.0, step=0.1)

    if st.button("Save Activity"):
        db.collection("activities").add({
            "user": user,
            "activity": activity,
            "duration": duration,
            "distance": distance,
            "timestamp": datetime.datetime.now().isoformat()
        })
        st.success("✅ Activity logged successfully!")


# --- DASHBOARD ---
def show_dashboard():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Leaderboard", "My Activity History", "Log Activity"])

    user = st.session_state["user"]

    if page == "Log Activity":
        log_activity(user)

    elif page == "Leaderboard":
        st.subheader("🏆 Monthly Leaderboard")
        activities = list(db.collection("activities").stream())
        data = [a.to_dict() for a in activities]

        if not data:
            st.info("No activities yet for this month.")
            return

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        current_month = datetime.datetime.now().month
        df = df[df["timestamp"].dt.month == current_month]

        # Simple points calculation
        df["points"] = df["duration"] * 1.5 + df["distance"] * 10
        leaderboard = df.groupby("user")["points"].sum().reset_index().sort_values(by="points", ascending=False)

        st.dataframe(leaderboard, use_container_width=True)

    elif page == "My Activity History":
        user_data = db.collection("activities").where("user", "==", user).stream()
        data = [d.to_dict() for d in user_data]

        if not data:
            st.info("No activities logged yet.")
            return

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        st.subheader("📈 Activity Over Time")
        fig = px.line(df, x="timestamp", y="duration", color="activity", title="Your Activity Timeline")
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            label="📥 Download Activity Data",
            data=df.to_csv(index=False),
            file_name="my_activity_history.csv",
            mime="text/csv"
        )


# --- APP ENTRY POINT ---
login_page()
