from flask import Flask, render_template, jsonify, request, Response
from microgrid import simulate_microgrid
import json
from datetime import datetime
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


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

@app.route("/agent/ask", methods=["POST"])
def agent_ask():
    global LAST_RESULT

    if not LAST_RESULT:
        return jsonify({"reply": "Run simulation first so I can analyze your microgrid data."})

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"reply": "Please type a question."})

    system_prompt = """
You are MicrogridAI Agent.
You help users understand microgrid simulation results and give recommendations.
Be simple, practical, and short.
If shortage is detected, give actionable steps.
"""

    user_prompt = f"""
Microgrid Latest Data (JSON):
{json.dumps(LAST_RESULT, indent=2)}

User Question:
{question}

Answer in simple words and bullet points.
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,
        max_tokens=400
    )

    reply = resp.choices[0].message.content
    return jsonify({"reply": reply})

@app.route("/agent/tune", methods=["POST"])
def agent_tune():
    global LAST_RESULT

    if not LAST_RESULT:
        return jsonify({
            "ok": False,
            "message": "Run simulation first so I can tune the microgrid."
        })

    system_prompt = """
You are MicrogridAI Auto-Tuning Agent.
Return ONLY valid JSON, no extra text.

Rules:
- If shortage exists, increase battery_cap and reduce homes.
- If stable, keep tuning minimal.
- Keep values realistic for demo.

Output JSON schema:
{
  "recommended": {
    "weather": "auto",
    "homes": 20,
    "batteryCap": 12,
    "interval": 10000
  },
  "reason": "short clear explanation"
}
"""

    user_prompt = f"""
Latest Microgrid Data (JSON):
{json.dumps(LAST_RESULT, indent=2)}

Tune the microgrid inputs to reduce shortage and stabilize the system.
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=350
    )

    text = resp.choices[0].message.content.strip()

    # ✅ Safe JSON parsing
    try:
        result = json.loads(text)
        return jsonify({"ok": True, **result})
    except Exception:
        return jsonify({
            "ok": False,
            "message": "Agent returned invalid JSON",
            "raw": text
        })
    
@app.route("/agent/forecast", methods=["POST"])
def agent_forecast():
    global LAST_RESULT

    if not LAST_RESULT:
        return jsonify({"ok": False, "message": "Run simulation first so I can forecast."})

    system_prompt = """
You are MicrogridAI Forecast Agent.
Return ONLY JSON (no markdown, no extra text).
Forecast next 6 hours based on latest microgrid data.

Output JSON schema:
{
  "forecast": [
    {"hour": 18, "solar_kw": 2.4, "demand_kw": 11.1, "supply_kw": 7.9, "risk": "HIGH"},
    ...
  ],
  "summary": "short summary"
}
Rules:
- solar goes down at evening/night
- demand increases in evening (6pm-11pm peak)
- keep values realistic
- risk can be LOW/MEDIUM/HIGH
"""

    user_prompt = f"""
Latest Microgrid Data (JSON):
{json.dumps(LAST_RESULT, indent=2)}

Generate next 6 hour forecast.
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )

    text = resp.choices[0].message.content.strip()

    try:
        result = json.loads(text)
        return jsonify({"ok": True, **result})
    except Exception:
        return jsonify({
            "ok": False,
            "message": "Agent returned invalid JSON",
            "raw": text
        })
    
@app.route("/agent/report", methods=["POST"])
def agent_report():
    global LAST_RESULT

    if not LAST_RESULT:
        return jsonify({"ok": False, "message": "Run simulation first so I can generate report."})

    system_prompt = """
You are MicrogridAI Report Generator.
Write a clean, professional report for hackathon/college SDG project.
Keep it structured and clear. Use headings and bullet points.
Do NOT include JSON, just plain text.
"""

    user_prompt = f"""
Generate a detailed project report based on latest microgrid simulation data:

SIMULATION DATA (JSON):
{json.dumps(LAST_RESULT, indent=2)}

Include:
1) Title
2) Problem Statement
3) Solution Overview
4) AI Used in Project
5) Current Simulation Summary
6) Forecast risk (general)
7) SDG 7 impact
8) Future Improvements
Make it easy to paste into PPT/report.
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.35,
        max_tokens=900
    )

    reply = resp.choices[0].message.content.strip()

    return jsonify({"ok": True, "report": reply})
@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")

if __name__ == "__main__":
    app.run(debug=True)
