import random
import requests
from datetime import datetime


# ✅ Auto location (Kurduvadi, Maharashtra)
DEFAULT_LAT = 18.13645
DEFAULT_LON = 75.44015


def get_real_weather(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """
    Fetch real-time weather using Open-Meteo (No API key required).

    Returns:
        cloud_cover (int): 0-100
        sunrise_hour (int)
        sunset_hour (int)
        sunrise_time (str)
        sunset_time (str)
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=cloud_cover"
        "&daily=sunrise,sunset"
        "&timezone=Asia%2FKolkata"
    )

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    cloud_cover = int(data["current"]["cloud_cover"])

    sunrise = data["daily"]["sunrise"][0]  # example: 2026-01-10T06:55
    sunset = data["daily"]["sunset"][0]    # example: 2026-01-10T18:14

    sunrise_hour = int(sunrise.split("T")[1].split(":")[0])
    sunset_hour = int(sunset.split("T")[1].split(":")[0])

    sunrise_time = sunrise.split("T")[1]
    sunset_time = sunset.split("T")[1]

    return cloud_cover, sunrise_hour, sunset_hour, sunrise_time, sunset_time


def simulate_microgrid(weather="auto", homes=20, battery_cap=10, lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """
    REAL Microgrid Simulator (Level 1)

    - weather=auto -> fetch real weather cloud cover
    - current_time is real system time (HH:MM:SS)
    - solar output changes smoothly using decimal time

    Parameters:
        weather (str): auto / sunny / cloudy / rainy
        homes (int): number of homes
        battery_cap (float): battery capacity in kWh
        lat/lon: location coordinates

    Returns:
        dict: simulation output (JSON ready)
    """

    # ✅ Real time
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second

    current_time = now.strftime("%H:%M:%S")

    # ✅ Decimal time for better solar simulation
    time_decimal = hour + (minute / 60) + (second / 3600)

    # ----------------------------
    # REAL WEATHER INPUT
    # ----------------------------
    sunrise_hour = 6
    sunset_hour = 18
    sunrise_time = "06:00"
    sunset_time = "18:00"

    if weather == "auto":
        try:
            cloud_cover, sunrise_hour, sunset_hour, sunrise_time, sunset_time = get_real_weather(lat, lon)
        except Exception:
            # fallback if API fails
            cloud_cover = 40
    else:
        # manual weather fallback
        cloud_cover = {"sunny": 10, "cloudy": 60, "rainy": 90}.get(weather, 40)

    # ----------------------------
    # SOLAR POWER OUTPUT
    # ----------------------------
    # cloud 0% -> solar factor 1.0
    # cloud 100% -> solar factor 0.2 (minimum)
    solar_factor = max(0.2, 1 - (cloud_cover / 100))

    panel_capacity_kw = 10  # assume 10kW solar plant

    if sunrise_hour <= time_decimal <= sunset_hour:
        # solar peak around mid-day
        mid = (sunrise_hour + sunset_hour) / 2
        denom = (mid - sunrise_hour) + 0.01

        base = max(0, 1 - abs(time_decimal - mid) / denom)
        solar_power = panel_capacity_kw * base * solar_factor
    else:
        solar_power = 0

    # ----------------------------
    # DEMAND SIMULATION (REALISTIC)
    # ----------------------------
    hospital_demand = 3.0  # always

    # school demand mainly day time
    school_demand = 2.0 if 8 <= hour <= 15 else 0.5

    # homes demand changes with time
    # night peak usage
    if 18 <= hour <= 23 or 0 <= hour <= 6:
        per_home = random.uniform(0.35, 0.55)
    else:
        per_home = random.uniform(0.20, 0.40)

    homes_demand = homes * per_home

    total_demand = hospital_demand + school_demand + homes_demand

    # ----------------------------
    # BATTERY SIMULATION
    # ----------------------------
    # battery % changes in real life, so keep it semi-random
    battery_level = random.randint(30, 95)
    battery_available = (battery_level / 100) * battery_cap

    total_supply = solar_power + battery_available

    # ----------------------------
    # PRIORITY DISTRIBUTION
    # ----------------------------
    remaining = total_supply

    hospital_given = min(hospital_demand, remaining)
    remaining -= hospital_given

    school_given = min(school_demand, remaining)
    remaining -= school_given

    homes_given = min(homes_demand, remaining)
    remaining -= homes_given

    # ----------------------------
    # ALERT SYSTEM
    # ----------------------------
    alert = "✅ Supply sufficient"
    if total_supply < total_demand:
        alert = "⚠️ Not enough energy. Low priority load reduced!"

    # ----------------------------
    # AI SUGGESTIONS ENGINE
    # ----------------------------
    suggestions = []

    # Daytime but solar low
    if sunrise_hour <= time_decimal <= sunset_hour and solar_power < 1:
        suggestions.append("⚠️ Solar output is very low during daytime. Check solar panel efficiency/shading.")

    # Heavy cloud cover
    if cloud_cover >= 70:
        suggestions.append(f"☁️ High cloud cover ({cloud_cover}%). Solar generation reduced.")
        suggestions.append("🔋 Use battery backup carefully during low solar production hours.")

    # Supply shortage
    if total_supply < total_demand:
        shortage = total_demand - total_supply
        suggestions.append(f"⚡ Energy shortage: {shortage:.2f} kW. Add solar panels or reduce load.")
        suggestions.append("🏠 Reduce home electricity usage during 6pm–11pm peak hours.")
        suggestions.append("🔋 Increase battery capacity for night & cloudy weather.")

    # Low battery level
    if battery_level < 35:
        suggestions.append("🔋 Battery is low. Charge battery during peak solar time (10am–2pm).")

    if not suggestions:
        suggestions.append("✅ Microgrid stable. Continue monitoring regularly.")

    # ----------------------------
    # FINAL RESPONSE
    # ----------------------------
    return {
        "current_time": current_time,
        "hour": hour,

        "weather": weather,
        "cloud_cover_percent": cloud_cover,
        "sunrise_time": sunrise_time,
        "sunset_time": sunset_time,

        "homes": homes,
        "battery_capacity_kwh": battery_cap,

        "solar_power_kw": round(solar_power, 2),
        "battery_level_percent": battery_level,
        "battery_support_kw": round(battery_available, 2),

        "total_demand_kw": round(total_demand, 2),
        "total_supply_kw": round(total_supply, 2),

        "distribution": {
            "hospital_kw": round(hospital_given, 2),
            "school_kw": round(school_given, 2),
            "homes_kw": round(homes_given, 2)
        },

        "alert": alert,
        "suggestions": suggestions
    }
