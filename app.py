import streamlit as st
from datetime import datetime
from firebase_config import db, bucket

st.set_page_config(page_title="Ripples in Motion Tracker", layout="wide")

# --- SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- NEW USER REGISTRATION ---
def register_user():
    st.header("Welcome to Ripples in Motion 🏃‍♂️")
    name = st.text_input("Name")
    dob = st.date_input("Date of Birth")
    phone = st.text_input("WhatsApp Number")
    photo = st.file_uploader("Upload Profile Picture (optional)", type=["jpg", "jpeg", "png"])
    if st.button("Register"):
        user_ref = db.collection("users").document(phone)
        data = {"name": name, "dob": str(dob), "phone": phone}
        if photo:
            blob = bucket.blob(f"profile_pics/{phone}.jpg")
            blob.upload_from_file(photo)
            data["photo_url"] = blob.public_url
        user_ref.set(data)
        st.session_state.user = phone
        st.success(f"Welcome, {name}!")
        st.rerun()

# --- ACTIVITY LOGGING ---
def log_activity(phone):
    st.subheader("📝 Log Your Activity")
    activity = st.selectbox("Activity Type", ["Walking", "Jogging", "Running", "Cycling", "Yoga", "Gym", "Dance", "Trekking", "Badminton"])
    duration = st.number_input("Duration (minutes)", min_value=1)
    date = st.date_input("Date", datetime.now().date())

    met_values = {
        "Walking": 3.5, "Jogging": 7, "Running": 9.8, "Cycling": 7.5,
        "Yoga": 3, "Gym": 6, "Dance": 5, "Trekking": 6.5, "Badminton": 5.5
    }
    calories = round(met_values[activity] * 70 * (duration / 60), 1)
    if st.button("Save Activity"):
        db.collection("activities").document(phone).collection("logs").add({
            "activity": activity,
            "duration": duration,
            "calories": calories,
            "date": str(date),
            "timestamp": datetime.now()
        })
        st.success(f"Activity logged: {activity} ({calories} kcal)")

# --- LEADERBOARD ---
def show_leaderboard():
    st.subheader("🏆 Monthly Leaderboard")
    current_month = datetime.now().strftime("%Y-%m")
    all_users = db.collection("users").stream()

    leaderboard = []
    for user in all_users:
        phone = user.id
        logs = db.collection("activities").document(phone).collection("logs").where("date", ">=", f"{current_month}-01").stream()
        total_calories = sum([l.to_dict()["calories"] for l in logs])
        leaderboard.append({
            "name": user.to_dict()["name"],
            "phone": phone,
            "calories": total_calories,
            "photo_url": user.to_dict().get("photo_url")
        })

    leaderboard = sorted(leaderboard, key=lambda x: x["calories"], reverse=True)
    top3 = leaderboard[:3]

    # --- Display top 3 performers ---
    cols = st.columns(3)
    for i, performer in enumerate(top3):
        with cols[i]:
            if performer["photo_url"]:
                st.image(performer["photo_url"], width=100)
            st.markdown(f"**#{i+1} {performer['name']}**")
            st.caption(f"{performer['calories']} kcal")

    # --- Show full leaderboard ---
    st.table([{ "Rank": i+1, "Name": x["name"], "Calories": x["calories"] } for i, x in enumerate(leaderboard)])

# --- USER DASHBOARD ---
if st.session_state.user:
    user_phone = st.session_state.user
    st.sidebar.success(f"Logged in as {user_phone}")
    choice = st.sidebar.radio("Navigation", ["Log Activity", "Leaderboard", "My Records"])
    if choice == "Log Activity":
        log_activity(user_phone)
    elif choice == "Leaderboard":
        show_leaderboard()
    else:
        st.subheader("📜 My Activity Records")
        logs = db.collection("activities").document(user_phone).collection("logs").order_by("date").stream()
        st.table([{**l.to_dict()} for l in logs])
else:
    register_user()
