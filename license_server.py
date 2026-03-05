from flask import Flask, request, jsonify
import json
import datetime
import hashlib

app = Flask(__name__)

# ---------- Load licenses ----------
with open("licenses.json", "r") as f:
    licenses = json.load(f)

# ---------- Active license sessions ----------
active_sessions = {}
# пример:
# {
#   "ABC123": {"ip": "1.2.3.4", "machine_id": "abcde123", "time": datetime}
# }

APP_VERSION = "2.5"
LOCK_MINUTES = 15  # минути до ослободување ако нема heartbeat

def hash_machine_id(machine_id):
    return hashlib.sha256(machine_id.encode()).hexdigest()

@app.route("/check_license", methods=["POST"])
def check_license():
    data = request.get_json()
    license_key = data.get("license")
    ip = data.get("ip")
    client_version = data.get("version", "")
    machine_id = data.get("machine_id", "")

    if client_version != APP_VERSION:
        return jsonify({"status": "OLD_VERSION", "message": "Update to 2.5"})

    if license_key not in licenses:
        return jsonify({"status": "BLOCKED", "message": "Invalid license"})

    now = datetime.datetime.now()
    expiry_date = datetime.datetime.strptime(
        licenses[license_key]["expiry"], "%Y-%m-%d"
    )

    if now > expiry_date:
        return jsonify({"status": "EXPIRED", "message": "License expired"})

    machine_hash = hash_machine_id(machine_id)
    session = active_sessions.get(license_key)

    if session:
        session_ip = session["ip"]
        session_machine = session["machine_id"]
        session_time = session["time"]
        diff = (now - session_time).total_seconds()

        if diff > LOCK_MINUTES * 60:
            # Ако поминале 15 минути без heartbeat → нова сесија
            active_sessions[license_key] = {
                "ip": ip,
                "machine_id": machine_hash,
                "time": now
            }
        else:
            if session_machine == machine_hash:
                # Иста машина → обнови време
                active_sessions[license_key]["time"] = now
            else:
                # Друга машина во рок од 15 минути
                return jsonify({
                    "status": "BLOCKED",
                    "message": "License already in use on another machine"
                })
    else:
        # Прво користење
        active_sessions[license_key] = {
            "ip": ip,
            "machine_id": machine_hash,
            "time": now
        }

    return jsonify({"status": "VALID", "message": "License OK"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
