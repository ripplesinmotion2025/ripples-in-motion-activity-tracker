def calculate_points(activity, distance_km, duration_min):
    if duration_min == 0:
        return 0
    pace = distance_km / duration_min  # km per min
    match activity:
        case "Walking": return (distance_km*8) + (pace*10)
        case "Jogging": return (distance_km*12) + (pace*20)
        case "Running": return (distance_km*18) + (pace*25)
        case "Cycling": return (distance_km*10) + (pace*15)
        case "Trekking": return duration_min*1.5
        case "Badminton": return duration_min*1.25
        case "Pickle Ball": return duration_min*1.0
        case "Volley Ball": return duration_min*0.8
        case "Gym": return duration_min*1.75
        case "Yoga": return duration_min*0.5
        case "Dance": return duration_min*1.0
        case _: return duration_min*1.0


def calculate_calories(activity, duration_min, weight_kg=70):
    if duration_min == 0:
        return 0
    METS = {
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
        "Dance": 5
    }
    met = METS.get(activity, 4)
    return round(met * weight_kg * (duration_min/60), 1)
