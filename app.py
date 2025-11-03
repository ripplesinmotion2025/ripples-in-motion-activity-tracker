# app.py
import streamlit as st
from datetime import datetime, date
import pandas as pd
import plotly.express as px
from firebase_config import db
from utils.activity_utils import calculate_points, calculate_calories

st.set_page_config(page_title="Ripples in Motion 🌊", layout="wide")

# ----------------- Utilities -----------------
def get_or_create_user(full_name: str):
    users_ref = db.collection("users")
    q = users_ref.where("full_name", "==", full_name).stream()
    doc = next(iter(q), None)
    if doc is None:
        new_ref = users_ref.document()
        new_ref.set({
            "full_name": full_name,
            "height": 0,
            "weight": 0,
            "created_at": datetime.now().isoformat()
        })
        return new_ref.id
    return doc.id

def fetch_user_logs(uid: str):
    coll = db.collection("activities").document(uid).collection("logs")
    docs = list(coll.stream())
    records = []
    for d in docs:
        rec = d.to_dict()
        rec["_id"] = d.id
        # ensure fields exist
        rec.setdefault("activity_type", "")
        rec.setdefault("distance", 0.0)
        rec.setdefault("duration", 0)
        rec.setdefault("points", 0)
        rec.setdefault("calories", 0)
        rec.setdefault("date", "")
        records.append(rec)
    return records

def save_activity(uid, activity_type, distance, duration, date_str, doc_id=None):
    points = float(calculate_points(activity_type, distance, duration))
    calories = float(calculate_calories(activity_type, duration))
    payload = {
        "activity_type": activity_type,
        "distance": float(distance),
        "duration": int(duration),
        "points": round(points,3),
        "calories": round(calories,1),
        "date": date_str,
        "updated_at": datetime.now().isoformat()
    }
    coll = db.collection("activities").document(uid).collection("logs")
    if doc_id:
        coll.document(doc_id).update(payload)
    else:
        coll.add(payload)
    return payload

def delete_activity(uid, doc_id):
    db.collection("activities").document(uid).collection("logs").document(doc_id).delete()

# ----------------- Leaderboard helpers -----------------
def monthly_aggregates():
    """Return dataframe with Name, Points, ActiveDays, TotalKM, TotalMins for current month"""
    current_month = datetime.now().strftime("%Y-%m")
    users = list(db.collection("users").stream())
    rows = []
    for u in users:
        uid = u.id
        user = u.to_dict()
        logs = db.collection("activities").document(uid).collection("logs").stream()
        pts = 0.0
        kms = 0.0
        mins = 0
        active_dates = set()
        for l in logs:
            rec = l.to_dict()
            d = rec.get("date","")
            if d.startswith(current_month):
                pts += float(rec.get("points",0) or 0)
                kms += float(rec.get("distance",0) or 0)
                mins += int(rec.get("duration",0) or 0)
                active_dates.add(d)
        rows.append({
            "uid": uid,
            "Name": user.get("full_name","Unknown"),
            "Points": round(pts,3),
            "ActiveDays": len(active_dates),
            "TotalKM": round(kms,2),
            "TotalMins": mins
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(["Points","ActiveDays"], ascending=False).reset_index(drop=True)
    df.index += 1
    df.insert(0, "Rank", df.index)
    return df

# ----------------- Heatmap helpers -----------------
def heatmap_month(df_logs, year:int, month:int, value_col="points"):
    """Create days x weekday heatmap matrix for a given year-month.
       Returns a DataFrame indexed by weekday (Mon..Sun) columns are week numbers with sums."""
    # filter
    df = df_logs.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'].dt.year==year) & (df['date'].dt.month==month)]
    if df.empty:
        return None
    df['day'] = df['date'].dt.day
    df['weekday'] = df['date'].dt.weekday  # Mon=0
    # get week of month (1..)
    df['weeknum'] = ((df['date'].dt.day - 1) // 7) + 1
    pivot = df.groupby(['weekday','weeknum'])[value_col].sum().unstack(fill_value=0)
    # reorder weekdays to Mon..Sun index 0..6
    pivot = pivot.reindex(index=[0,1,2,3,4,5,6]).fillna(0)
    pivot.index = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    return pivot

def heatmap_year(df_logs, year:int, value_col="points"):
    """Return matrix month vs day-of-month aggregated by value_col for a year for heatmap-like visualization"""
    df = df_logs.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.year==year]
    if df.empty:
        return None
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    pivot = df.groupby(['month','day'])[value_col].sum().unstack(fill_value=0)
    # ensure months 1..12 present
    pivot = pivot.reindex(index=range(1,13), fill_value=0)
    pivot.index = [datetime(year, m, 1).strftime('%b') for m in pivot.index]
    return pivot

# ----------------- UI: main -----------------
st.title("🌊 Ripples in Motion - Activity Tracker")
st.markdown("**Quick select your name and start logging / editing activities.**")

# Name selection (pre-populated list)
names_list = [
    "Prem Kumar R","Aswin","Selvi SenthilKumar","Kamalesh","Rashmi","Anu Anu","Gowtham","Harine",
    "Shakthi","Sindhu","Ram Prasad","Selvarani","Sowmya","Deepana","Remya","Gokul","Mahima","Umarani",
    "Selvi","Mani","Selvam","Srimathi","Navin","Durai","Nithya"
]
# Allow custom name by typing "Other"
choice = st.selectbox("Pick your name (or type a new name below)", names_list + ["Other"])
if choice == "Other":
    full_name = st.text_input("Enter your name")
else:
    full_name = choice

if full_name and st.button("Continue"):
    uid = get_or_create_user(full_name.strip())
    st.session_state["user_name"] = full_name.strip()
    st.session_state["uid"] = uid
    st.experimental_rerun()

if "user_name" not in st.session_state:
    st.info("Select or type your name and click Continue to proceed.")
    st.stop()

uid = st.session_state["uid"]
full_name = st.session_state["user_name"]

# Sidebar navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2764/2764434.png", width=100)
st.sidebar.markdown(f"**Hello, {full_name}**")
menu = st.sidebar.radio("Navigate", ["Leaderboard","Log Activity","Edit / Delete Activities","My History","Profile"])

# ---------- Leaderboard ----------
if menu == "Leaderboard":
    st.header("🏆 Monthly Leaderboard")
    df_lb = monthly_aggregates()
    if df_lb.empty:
        st.info("No activity data for this month yet.")
    else:
        # Highlight top 3
        top3 = df_lb.head(3)
        cols = st.columns(3)
        medals = ["🥇","🥈","🥉"]
        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                st.markdown(f"### {medals[i]} {row['Name']}")
                st.metric("Points", row["Points"])
                st.write(f"Active Days: {row['ActiveDays']}")
                st.write(f"KM: {row['TotalKM']} | Mins: {row['TotalMins']}")

        st.divider()
        st.subheader("Full Leaderboard (This Month)")
        st.dataframe(df_lb[["Rank","Name","Points","ActiveDays","TotalKM","TotalMins"]], use_container_width=True)

# ---------- Log Activity ----------
elif menu == "Log Activity":
    st.header(f"📝 Log Activity — {full_name}")
    activities = [
        "Walking","Jogging","Running","Cycling","Trekking","Badminton","Pickle Ball","Volley Ball",
        "Gym","Yoga/Meditation","Dance","Swimming","Table Tennis","Tennis","Cricket","Football"
    ]
    with st.form("log_form"):
        act = st.selectbox("Activity", activities)
        dist = st.number_input("Distance (km)", min_value=0.0, step=0.1, format="%.2f")
        dur = st.number_input("Duration (mins)", min_value=0, step=1)
        d = st.date_input("Date", date.today())
        submitted = st.form_submit_button("Save")
    if submitted:
        payload = save_activity(uid, act, dist, dur, d.strftime("%Y-%m-%d"))
        st.success(f"Saved: {act} — {payload['points']} pts, {payload['calories']} kcal")

# ---------- Edit / Delete Activities ----------
elif menu == "Edit / Delete Activities":
    st.header("✏️ Edit / Delete Your Activities")
    records = fetch_user_logs(uid)
    if not records:
        st.info("You have no activities to edit.")
    else:
        # show as table with index and small controls
        df = pd.DataFrame(records)
        df_display = df[["date","activity_type","distance","duration","points","calories","_id"]].sort_values("date", ascending=False)
        st.dataframe(df_display.drop(columns=["_id"]), use_container_width=True)

        st.markdown("**Click an entry below to edit or delete**")
        for rec in sorted(records, key=lambda x: x["date"], reverse=True):
            exp = st.expander(f"{rec['date']} — {rec['activity_type']} — {rec['points']} pts")
            with exp:
                col1, col2 = st.columns(2)
                with col1:
                    new_act = st.selectbox("Activity", options=activities, index=activities.index(rec["activity_type"]) if rec["activity_type"] in activities else 0, key=f"act_{rec['_id']}")
                    new_dist = st.number_input("Distance (km)", value=float(rec.get("distance",0.0)), key=f"dist_{rec['_id']}")
                with col2:
                    new_dur = st.number_input("Duration (mins)", value=int(rec.get("duration",0)), key=f"dur_{rec['_id']}")
                    new_date = st.date_input("Date", value=pd.to_datetime(rec.get("date")).date(), key=f"date_{rec['_id']}")
                col3, col4 = st.columns(2)
                if col3.button("Update", key=f"upd_{rec['_id']}"):
                    save_activity(uid, new_act, new_dist, new_dur, new_date.strftime("%Y-%m-%d"), doc_id=rec["_id"])
                    st.success("Updated successfully.")
                    st.experimental_rerun()
                if col4.button("Delete", key=f"del_{rec['_id']}"):
                    delete_activity(uid, rec["_id"])
                    st.warning("Deleted.")
                    st.experimental_rerun()

# ---------- My History (charts & heatmaps) ----------
elif menu == "My History":
    st.header("📈 My Activity History & Heatmaps")
    recs = fetch_user_logs(uid)
    if not recs:
        st.info("No activity records yet.")
    else:
        df = pd.DataFrame(recs)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        # summary cards
        total_points = df['points'].sum()
        total_km = df['distance'].sum()
        total_mins = df['duration'].sum()
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Points", round(total_points,2))
        c2.metric("Total KM", round(total_km,2))
        c3.metric("Total Duration (mins)", int(total_mins))

        st.subheader("Points over time")
        st.line_chart(df.set_index('date')['points'])

        st.subheader("Points by activity type")
        agg = df.groupby('activity_type')['points'].sum().reset_index().sort_values('points', ascending=False)
        fig_bar = px.bar(agg, x='activity_type', y='points', title="Points by Activity")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Monthly heatmap selector
        st.divider()
        st.subheader("Monthly Heatmap (days of month by weekday)")
        st.write("Select month and year to view day-by-week heatmap (intensity by points)")
        years = sorted(df['date'].dt.year.unique(), reverse=True)
        sel_year = st.selectbox("Year", years, index=0)
        months = sorted(df[df['date'].dt.year==sel_year]['date'].dt.month.unique(), reverse=True)
        sel_month = st.selectbox("Month (number)", months, index=0)

        pivot_m = heatmap_month(df, int(sel_year), int(sel_month), value_col="points")
        if pivot_m is None:
            st.info("No data for this month.")
        else:
            fig = px.imshow(pivot_m, labels=dict(x="Week of month", y="Weekday", color="Points"),
                            x=pivot_m.columns.astype(str), y=pivot_m.index, title=f"Heatmap: {sel_year}-{sel_month:02d}")
            st.plotly_chart(fig, use_container_width=True)

        # Yearly heatmap
        st.divider()
        st.subheader("Yearly Heatmap (month vs day)")
        year_for_heat = st.selectbox("Select year for yearly heatmap", years, index=0, key="yrheat")
        pivot_y = heatmap_year(df, int(year_for_heat), value_col="points")
        if pivot_y is None:
            st.info("No data for this year.")
        else:
            # plotly heatmap where y=month, x=day
            fig2 = px.imshow(pivot_y.fillna(0),
                             labels=dict(x="Day of month", y="Month", color="Points"),
                             x=pivot_y.columns.astype(str), y=pivot_y.index,
                             title=f"Yearly Heatmap: {year_for_heat}")
            st.plotly_chart(fig2, use_container_width=True)

        # Download full history
        st.divider()
        csv = df.drop(columns=['_id']).to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download full history (CSV)", csv, file_name=f"{full_name}_activity_history.csv", mime="text/csv")

# ---------- Profile ----------
elif menu == "Profile":
    st.header("🧑‍💻 My Profile")
    user_doc = db.collection("users").document(uid).get()
    data = user_doc.to_dict() if user_doc.exists else {}
    with st.form("profile_form"):
        name = st.text_input("Full name", value=data.get("full_name", full_name))
        height = st.number_input("Height (cm)", value=float(data.get("height",0.0)))
        weight = st.number_input("Weight (kg)", value=float(data.get("weight",0.0)))
        submitted = st.form_submit_button("Update Profile")
    if submitted:
        db.collection("users").document(uid).update({
            "full_name": name,
            "height": float(height),
            "weight": float(weight)
        })
        st.success("Profile updated.")
        st.experimental_rerun()
