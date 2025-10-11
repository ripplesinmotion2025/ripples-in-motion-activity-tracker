def calculate_points(activity, distance_km, duration_min):
    if duration_min == 0:
        return 0
    pace = distance_km / duration_min  # km per min
    match activity:
        case "Walking": return (distance_km*10) + (pace*10)
        case "Jogging": return (distance_km*12) + (pace*20)
        case "Running": return (distance_km*15) + (pace*20)
        case "Cycling": return (distance_km*10) + (pace*15)
        case "Trekking": return duration_min*0.85
        case "Badminton": return duration_min*0.75
        case "Pickle Ball": return duration_min*0.75
        case "Volley Ball": return duration_min*0.75
        case "Gym": return duration_min*0.85
        case "Yoga/Meditation": return duration_min*0.75
        case "Dance": return duration_min*0.8
        case "Swimming": return duration_min*1.0
        case "Table Tennis": return duration_min*0.85
        case "Tennis": return duration_min*0.9
        case "Cricket": return duration_min*0.65
        case "Foot Ball": return duration_min*0.9
        case _: return duration_min*0.75


def calculate_calories(activity, duration_min, weight_kg=70):
    if duration_min == 0:
        return 0
    METS = {
        "Walking": 3.5,
        "Jogging": 7,
        "Running": 9,
        "Cycling": 7.5,
        "Trekking": 6.5,
        "Badminton": 5.5,
        "Pickle Ball": 6,
        "Volley Ball": 5,
        "Gym": 6,
        "Yoga/Meditation": 3,
        "Dance": 8,
        "Swimming": 9,
        "Table Tennis": 7.5,
        "Tennis": 8,
        "Cricket": 5,
        "Foot ball": 7.5
    }
    met = METS.get(activity, 4)
    return round(met * weight_kg * (duration_min/60), 1)
