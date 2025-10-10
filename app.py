import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
from firebase_admin import auth

from firebase_config import  db

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Ripples in Motion 🌊", layout="wide")

# ---------------- Helper Functions ----------------
def register_user():
    st.header("🏁 Register for Ripples in Motion")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    dob_year = st.selectbox("Year of Birth", options=list(range(1950, datetime.now().year + 1)))
    phone = st.text_input("Phone / WhatsApp Number")
    height = st.number_input("Height (cm)", min_value=0.0, format="%.1f")
    weight = st.number_input("Weight (kg)", min_value=0.0, format="%.1f")

    if st.button("Register"):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            uid = user["localId"]

            db.collection("users").document(uid).set({
                "full_name": full_name,
                "email": email,
                "dob_year": dob_year,
                "phone": phone,
                "height": height,
                "weight": weight,
                "points": 0
            })

            st.success("🎉 Registered successfully! Please log in.")
            st.session_state["show_login"] = True
            st.rerun()
        except Exception as e:
            st.error(f"Registration failed: {e}")


def login_user():
    st.header("🔐 Login to Continue")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state["user"] = user
            st.success("Welcome back!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")


def show_leaderboard():
    st.title("🏆 Monthly Leaderboard")
    current_month = datetime.now().strftime("%Y-%m")

    users_ref = db.collection("users").stream()
    data = []
    for doc in users_ref:
        user = doc.to_dict()
        uid = doc.id
        total_points = 0

        activities_ref = db.collection("activities").document(uid).collection("logs").stream()
        for act_doc in activities_ref:
            act = act_doc.to_dict()
            if act["date"].startswith(current_month):
                total_points += act["points"]

        data.append({"Name": user.get("full_name"), "Points": total_points})

    df = pd.DataFrame(data).sort_values(by="Points", ascending=False)
    df["Rank"] = range(1, len(df) + 1)
    st.dataframe(df, use_container_width=True)

    if len(df) >= 3:
        st.markdown(f"🥇 **{df.iloc[0]['Name']}** | 🥈 **{df.iloc[1]['Name']}** | 🥉 **{df.iloc[2]['Name']}**")


def log_activity(uid):
    st.title("📝 Log Your Daily Activity")

    activity_type = st.selectbox("Select Activity", ["Running", "Walking", "Cycling", "Swimming", "Gym Workout"])
    distance = st.number_input("Distance (in km)", min_value=0.0, format="%.2f")
    duration = st.number_input("Duration (in minutes)", min_value=0)
    date = st.date_input("Date", datetime.now())

    if st.button("Save Activity"):
        points = int(distance * 10)
        db.collection("activities").document(uid).collection("logs").add({
            "activity_type": activity_type,
            "distance": distance,
            "duration": duration,
            "points": points,
            "date": date.strftime("%Y-%m-%d")
        })
        st.success(f"✅ {activity_type} logged successfully! (+{points} points)")


def view_history(uid):
    st.title("📈 My Activity History")
    activities = db.collection("activities").document(uid).collection("logs").stream()
    data = [a.to_dict() for a in activities]
    if not data:
        st.info("No activities logged yet.")
        return

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    st.line_chart(df.set_index("date")["points"])

    fig = px.bar(df, x="date", y="points", color="activity_type", title="Points Over Time")
    st.plotly_chart(fig, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv, file_name="my_activity_history.csv", mime="text/csv")


def edit_profile(uid):
    st.title("🧑‍💻 Edit My Profile")

    user_ref = db.collection("users").document(uid)
    user_data = user_ref.get().to_dict()

    with st.form("edit_profile_form"):
        phone = st.text_input("Phone / WhatsApp Number", user_data.get("phone", ""))
        height = st.number_input("Height (cm)", min_value=0.0, value=float(user_data.get("height", 0.0)), format="%.1f")
        weight = st.number_input("Weight (kg)", min_value=0.0, value=float(user_data.get("weight", 0.0)), format="%.1f")
        submitted = st.form_submit_button("Update Profile")

        if submitted:
            user_ref.update({
                "phone": phone,
                "height": height,
                "weight": weight
            })
            st.success("✅ Profile updated successfully!")


def show_dashboard():
    user = st.session_state["user"]
    uid = user["localId"]
    user_data = db.collection("users").document(uid).get().to_dict()

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2764/2764434.png", width=100)
        st.header(f"Welcome, {user_data.get('full_name', 'User')} 👋")
        choice = st.radio("Navigate", ["🏆 Leaderboard", "📝 Log Activity", "📈 My History", "🧑‍💻 Edit Profile"])
        if st.button("Logout"):
            del st.session_state["user"]
            st.success("Logged out successfully!")
            st.rerun()

    if choice == "🏆 Leaderboard":
        show_leaderboard()
    elif choice == "📝 Log Activity":
        log_activity(uid)
    elif choice == "📈 My History":
        view_history(uid)
    else:
        edit_profile(uid)


# ------------------------ Main App ------------------------
st.title("🌊 Ripples in Motion - Activity Tracker")

if "user" in st.session_state:
    show_dashboard()
else:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        login_user()
    with tab2:
        register_user()
