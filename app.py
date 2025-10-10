import streamlit as st
import datetime
from firebase_config import db

st.set_page_config(page_title="Ripples in Motion Activity Tracker", layout="centered")

# --------------------------------
# Helper: Calorie Calculation
# --------------------------------
def calculate_calories(activity, duration, weight=70):
    """Estimate calories burned using MET values."""
    MET_VALUES = {
        "Walking": 3.5,
        "Jogging": 7,
        "Running": 9.8,
        "Cycling": 7.5,
        "Trekking": 6.5,
        "Badminton": 5.5,
        "Pickle Ball": 5,
        "Volley Ball": 4,
        "Gym": 6,
        "Yoga": 3,
        "Dance": 5,
        "Swimming": 8,
        "Skipping": 10,
        "Workout": 6.5
    }
    met = MET_VALUES.get(activity, 4)
    calories = round(met * weight * (duration / 60), 1)
    return calories


# --------------------------------
# User Registration
# --------------------------------
def register_user():
    st.subheader("🧍 Register or Login")
    name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth")
    phone = st.text_input("WhatsApp Number")

    if st.button("Register / Login"):
        if name and phone:
            user_ref = db.collection("users").document(phone)
            user_doc = user_ref.get()

            if user_doc.exists:
                st.success(f"Welcome back, {user_doc.to_dict()['name']}! ✅")
            else:
                user_ref.set({
                    "name": name,
                    "dob": dob.strftime("%Y-%m-%d"),
                    "phone": phone,
                    "created_at": datetime.datetime.now()
                })
                st.success(f"🎉 {name} registered successfully!")

            st.session_state["user_phone"] = phone
            st.rerun()
        else:
            st.warning("⚠️ Please fill in all details before proceeding.")


# --------------------------------
# Log Activity
# --------------------------------
def log_activity():
    st.subheader("🏃‍♀️ Log Your Activity")
    phone = st.session_state.get("user_phone")
    if not phone:
        st.warning("Please register or log in first.")
        return

    activities = [
        "Running", "Walking", "Cycling", "Jogging", "Yoga", "Swimming",
        "Skipping", "Workout", "Trekking", "Badminton", "Pickle Ball",
        "Volley Ball", "Dance", "Gym"
    ]

    selected_activity = st.selectbox("Select Activity", activities)
    duration = st.number_input("Duration (in minutes)", min_value=1)
    date = st.date_input("Activity Date", datetime.date.today())

    calories = calculate_calories(selected_activity, duration)
    st.info(f"🔥 Estimated Calories Burned: **{calories} kcal**")

    if st.button("Submit Activity"):
        db.collection("activities").add({
            "phone": phone,
            "activity": selected_activity,
            "duration": duration,
            "calories": calories,
            "date": date.strftime("%Y-%m-%d"),
            "timestamp": datetime.datetime.now()
        })
        st.success(f"✅ {selected_activity} logged successfully for {date}!")
        st.balloons()


# --------------------------------
# Leaderboard
# --------------------------------
def show_leaderboard():
    st.subheader("🏆 Leaderboard (This Month)")

    activities_ref = db.collection("activities")

    start_month = datetime.date.today().replace(day=1)
    end_month = datetime.date.today()

    query = activities_ref.where("date", ">=", start_month.strftime("%Y-%m-%d")) \
                          .where("date", "<=", end_month.strftime("%Y-%m-%d"))
    results = query.stream()

    data = {}
    for doc in results:
        entry = doc.to_dict()
        phone = entry.get("phone")
        calories = entry.get("calories", 0)

        data[phone] = data.get(phone, 0) + calories

    if not data:
        st.info("No activities logged for this month yet.")
        return

    leaderboard = []
    for phone, total_cal in data.items():
        user_doc = db.collection("users").document(phone).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            leaderboard.append({
                "name": user_data["name"],
                "phone": phone,
                "total_calories": total_cal
            })

    leaderboard = sorted(leaderboard, key=lambda x: x["total_calories"], reverse=True)

    st.write("### 🥇 Top 3 Performers This Month")
    for i, user in enumerate(leaderboard[:3]):
        st.markdown(f"**{i+1}. {user['name']} — {round(user['total_calories'], 1)} kcal**")

    st.divider()
    st.write("### 📋 Full Leaderboard (By Calories Burned)")
    st.dataframe(leaderboard)


# --------------------------------
# View Past Activities
# --------------------------------
def view_my_activities():
    st.subheader("📅 My Past Activities")
    phone = st.session_state.get("user_phone")
    if not phone:
        st.warning("Please register or log in first.")
        return

    activities_ref = db.collection("activities").where("phone", "==", phone)
    results = activities_ref.stream()

    records = []
    for doc in results:
        record = doc.to_dict()
        records.append({
            "Date": record.get("date"),
            "Activity": record.get("activity"),
            "Duration (mins)": record.get("duration"),
            "Calories (kcal)": record.get("calories")
        })

    if not records:
        st.info("You haven’t logged any activities yet.")
    else:
        records = sorted(records, key=lambda x: x["Date"], reverse=True)
        st.dataframe(records)
        total_time = sum([r["Duration (mins)"] for r in records])
        total_calories = sum([r["Calories (kcal)"] for r in records])
        st.success(f"⏱️ Total Time: **{total_time} mins**, 🔥 Total Calories: **{round(total_calories,1)} kcal**")


# --------------------------------
# Streamlit App Layout
# --------------------------------
st.title("🏃‍♂️ Ripples in Motion Activity Tracker")

menu = ["Register / Login", "Log Activity", "Leaderboard", "My Past Activities"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Register / Login":
    register_user()
elif choice == "Log Activity":
    log_activity()
elif choice == "Leaderboard":
    show_leaderboard()
elif choice == "My Past Activities":
    view_my_activities()
