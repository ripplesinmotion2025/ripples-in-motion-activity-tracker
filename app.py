import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
from firebase_config import db
from utils.activity_utils import calculate_points, calculate_calories

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Ripples in Motion 🌊", layout="wide")

# ---------------- Helper Functions ----------------
def get_or_create_user(full_name):
    users_ref = db.collection("users")
    query = users_ref.where("full_name", "==", full_name).stream()
    user_doc = None

    for doc in query:
        user_doc = doc
        break

    if not user_doc:
        new_user_ref = users_ref.document()
        new_user_ref.set({
            "full_name": full_name,
            "height": 0,
            "weight": 0,
            "points": 0,
            "created_at": datetime.now().isoformat()
        })
        return new_user_ref.id
    else:
        return user_doc.id


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

    if not data:
        st.info("No users found yet.")
        return

    df = pd.DataFrame(data).sort_values(by="Points", ascending=False)
    df["Rank"] = range(1, len(df) + 1)
    st.dataframe(df, use_container_width=True)

    if len(df) >= 3:
        st.markdown(f"🥇 **{df.iloc[0]['Name']}** | 🥈 **{df.iloc[1]['Name']}** | 🥉 **{df.iloc[2]['Name']}**")


def log_activity(uid, full_name):
    st.title(f"📝 Log Activity for {full_name}")

    activity_type = st.selectbox("Select Activity", ["Walking",
        "Jogging",
        "Running",
        "Cycling",
        "Trekking",
        "Badminton",
        "Pickle Ball",
        "Volley Ball",
        "Gym",
        "Yoga/Meditation",
        "Dance",
        "Swimming",
        "Table Tennis",
        "Tennis",
        "Cricket",
        "Foot ball"])

    distance = st.number_input("Distance (in km)", min_value=0.0, format="%.2f")
    duration = st.number_input("Duration (in minutes)", min_value=0)
    date = st.date_input("Date", datetime.now())

    if st.button("Save Activity"):
        points = int(calculate_points(activity_type, distance, duration))
        calories = int(calculate_calories(activity_type,duration))
        db.collection("activities").document(uid).collection("logs").add({
            "activity_type": activity_type,
            "distance": distance,
            "duration": duration,
            "points": points,
            "calories": calories,
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
    st.title("🧑‍💻 Update My Details")

    user_ref = db.collection("users").document(uid)
    user_data = user_ref.get().to_dict()

    with st.form("edit_profile_form"):
        height = st.number_input("Height (cm)", min_value=0.0, value=float(user_data.get("height", 0.0)), format="%.1f")
        weight = st.number_input("Weight (kg)", min_value=0.0, value=float(user_data.get("weight", 0.0)), format="%.1f")
        submitted = st.form_submit_button("Update Profile")

        if submitted:
            user_ref.update({"height": height, "weight": weight})
            st.success("✅ Profile updated successfully!")


def show_dashboard(uid, full_name):
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2764/2764434.png", width=100)
        st.header(f"Welcome, {full_name} 👋")
        choice = st.radio("Navigate", ["🏆 Leaderboard", "📝 Log Activity", "📈 My History", "🧑‍💻 Edit Profile"])
        if st.button("Change User"):
            del st.session_state["user_name"]
            st.rerun()

    if choice == "🏆 Leaderboard":
        show_leaderboard()
    elif choice == "📝 Log Activity":
        log_activity(uid, full_name)
    elif choice == "📈 My History":
        view_history(uid)
    else:
        edit_profile(uid)


# ------------------------ Main App ------------------------
st.title("🌊 Ripples in Motion - Activity Tracker")

if "user_name" not in st.session_state:
    full_name = st.selectbox("Enter Your Name to Continue", ["Prem Kumar R",
        "Aswin",
        "Selvi SenthilKumar",
        "Kamalesh",
        "Rashmi",
        "Anu Anu",
        "Gowtham",
        "Harine",
        "Shakthi",
        "Sindhu",
        "Ram Prasad",
        "Selvarani",
        "Sowmya",
        "Deepana",
        "Remya",
        "Gokul",
        "Mahima",
        "Umarani",
        "Selvi",
        "Mani",
        "Selvam",
        "Srimathi",
        "Navin",
        "Durai",
        "Nithya"])
    if st.button("Continue"):
        if full_name.strip():
            uid = get_or_create_user(full_name.strip())
            st.session_state["user_name"] = full_name.strip()
            st.session_state["uid"] = uid
            st.success(f"Welcome, {full_name}! Let's begin 🌊")
            st.rerun()
        else:
            st.warning("Please enter a valid name to continue.")
else:
    show_dashboard(st.session_state["uid"], st.session_state["user_name"])
