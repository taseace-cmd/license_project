from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

# ---------- Load licenses ----------
with open("licenses.json", "r") as f:
    licenses = json.load(f)

# ---------- Soft lock storage ----------
last_use = {}  # {"license_key": {"ip": datetime}}

# ---------- Config ----------
APP_VERSION = "2.5"
SOFT_LOCK_MINUTES = 15

# ---------- License check endpoint ----------
@app.route("/check_license", methods=["POST"])
def check_license_route():
    data = request.get_json()
    license_key = data.get("license")
    ip = data.get("ip")
    client_version = data.get("version", "")

    # --- Version check ---
    if client_version != APP_VERSION:
        return jsonify({"status": "OLD_VERSION", "message": "Update to version 2.5"})

    # --- License exists? ---
    if license_key not in licenses:
        return jsonify({"status": "BLOCKED", "message": "Invalid license"})

    # --- Soft lock check ---
    now = datetime.datetime.now()
    ip_times = last_use.get(license_key, {})
    last_time = ip_times.get(ip)
    if last_time and (now - last_time).total_seconds() < SOFT_LOCK_MINUTES * 60:
        return jsonify({"status": "BLOCKED", "message": f"Soft lock active. Wait {SOFT_LOCK_MINUTES} min"})

    # --- Expiry check ---
    expiry_date = datetime.datetime.strptime(licenses[license_key]["expiry"], "%Y-%m-%d")
    if now > expiry_date:
        return jsonify({"status": "EXPIRED", "message": "License expired"})

    # --- Valid license ---
    ip_times[ip] = now
    last_use[license_key] = ip_times
    return jsonify({"status": "VALID", "message": "License OK"})

# ---------- Run server ----------
if __name__ == "__main__":
    # Host 0.0.0.0 за пристап од други компјутери, port 5000
    app.run(host="0.0.0.0", port=5000)
