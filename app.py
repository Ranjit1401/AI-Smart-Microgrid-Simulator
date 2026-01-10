from flask import Flask, render_template, jsonify, request, Response
from microgrid import simulate_microgrid
import json
from datetime import datetime

app = Flask(__name__)

# ✅ Store last simulation result globally
LAST_RESULT = None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/simulate")
def simulate():
    global LAST_RESULT

    weather = request.args.get("weather", "sunny")
    homes = int(request.args.get("homes", 20))
    battery_cap = float(request.args.get("batteryCap", 10))

    result = simulate_microgrid(weather=weather, homes=homes, battery_cap=battery_cap)

    # store latest
    LAST_RESULT = result

    return jsonify(result)


@app.route("/download/json")
def download_json():
    global LAST_RESULT

    if not LAST_RESULT:
        return "No simulation has been run yet.", 400

    filename = f"microgrid_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    content = json.dumps(LAST_RESULT, indent=2)

    return Response(
        content,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@app.route("/download/txt")
def download_txt():
    global LAST_RESULT

    if not LAST_RESULT:
        return "No simulation has been run yet.", 400

    r = LAST_RESULT
    dist = r["distribution"]

    lines = []
    lines.append("AI SMART MICROGRID REPORT (SDG 7)")
    lines.append("=" * 40)
    lines.append(f"Hour: {r['hour']}")
    lines.append(f"Weather: {r['weather']}")
    lines.append(f"Homes: {r['homes']}")
    lines.append(f"Battery Capacity (kWh): {r['battery_capacity_kwh']}")
    lines.append("-" * 40)
    lines.append(f"Solar Power (kW): {r['solar_power_kw']}")
    lines.append(f"Battery Level (%): {r['battery_level_percent']}")
    lines.append(f"Battery Support (kW): {r['battery_support_kw']}")
    lines.append(f"Total Demand (kW): {r['total_demand_kw']}")
    lines.append(f"Total Supply (kW): {r['total_supply_kw']}")
    lines.append("-" * 40)
    lines.append("Power Distribution (kW):")
    lines.append(f"  Hospital: {dist['hospital_kw']}")
    lines.append(f"  School:   {dist['school_kw']}")
    lines.append(f"  Homes:    {dist['homes_kw']}")
    lines.append("-" * 40)
    lines.append(f"Alert: {r['alert']}")
    lines.append("-" * 40)
    lines.append("AI Suggestions:")
    for s in r.get("suggestions", []):
        lines.append(f" - {s}")

    content = "\n".join(lines)

    filename = f"microgrid_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


if __name__ == "__main__":
    app.run(debug=True)
