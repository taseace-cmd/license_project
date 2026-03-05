from flask import Flask, request, jsonify
import json
import datetime
import hashlib

app = Flask(__name__)

with open("licenses.json", "r") as f:
    licenses = json.load(f)

active_sessions = {}

APP_VERSION = "2.5"
LOCK_MINUTES = 15


def hash_machine_id(machine_id):
    return hashlib.sha256(machine_id.encode()).hexdigest()


@app.route("/check_license", methods=["POST"])
def check_license():

    data = request.get_json()

    license_key = data.get("license")
    ip = data.get("ip")
    machine_id = data.get("machine_id")
    client_version = data.get("version", "")

    if client_version != APP_VERSION:
        return jsonify({
            "status": "OLD_VERSION",
            "message": "Update to version 2.5"
        })

    if license_key not in licenses:
        return jsonify({
            "status": "BLOCKED",
            "message": "Invalid license"
        })

    now = datetime.datetime.now()

    expiry_date = datetime.datetime.strptime(
        licenses[license_key]["expiry"],
        "%Y-%m-%d"
    )

    if now > expiry_date:
        return jsonify({
            "status": "EXPIRED",
            "message": "License expired"
        })

    machine_hash = hash_machine_id(machine_id)

    session = active_sessions.get(license_key)

    if session:

        session_machine = session["machine_id"]
        last_time = session["time"]

        diff = (now - last_time).total_seconds()

        if diff > LOCK_MINUTES * 60:

            active_sessions[license_key] = {
                "ip": ip,
                "machine_id": machine_hash,
                "time": now
            }

        else:

            if session_machine == machine_hash:

                active_sessions[license_key]["time"] = now

            else:

                return jsonify({
                    "status": "BLOCKED",
                    "message": "License already in use"
                })

    else:

        active_sessions[license_key] = {
            "ip": ip,
            "machine_id": machine_hash,
            "time": now
        }

    return jsonify({
        "status": "VALID",
        "message": "License OK"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
