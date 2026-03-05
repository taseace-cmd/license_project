from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

# ---------- Load licenses ----------
with open("licenses.json", "r") as f:
    licenses = json.load(f)

# ---------- Active license sessions ----------
active_sessions = {}
# пример:
# {
#   "ABC123": {"ip": "1.2.3.4", "time": datetime}
# }

APP_VERSION = "2.5"
LOCK_MINUTES = 15


@app.route("/check_license", methods=["POST"])
def check_license():

    data = request.get_json()

    license_key = data.get("license")
    ip = data.get("ip")
    client_version = data.get("version", "")

    # ---------- VERSION CHECK ----------
    if client_version != APP_VERSION:
        return jsonify({"status": "OLD_VERSION", "message": "Update to 2.5"})


    # ---------- LICENSE EXISTS ----------
    if license_key not in licenses:
        return jsonify({"status": "BLOCKED", "message": "Invalid license"})


    now = datetime.datetime.now()


    # ---------- EXPIRY CHECK ----------
    expiry_date = datetime.datetime.strptime(
        licenses[license_key]["expiry"], "%Y-%m-%d"
    )

    if now > expiry_date:
        return jsonify({"status": "EXPIRED", "message": "License expired"})


    # ---------- IP LOCK LOGIC ----------
    session = active_sessions.get(license_key)

    if session:

        session_ip = session["ip"]
        session_time = session["time"]

        diff = (now - session_time).total_seconds()

        # ако поминале 15 минути → нова сесија
        if diff > LOCK_MINUTES * 60:
            active_sessions[license_key] = {
                "ip": ip,
                "time": now
            }

        else:
            # ако е иста IP → дозволи и освежи време
            if session_ip == ip:

                active_sessions[license_key]["time"] = now

            else:
                # друга IP во рок од 15 мин
                return jsonify({
                    "status": "BLOCKED",
                    "message": "License already in use"
                })

    else:
        # прво користење
        active_sessions[license_key] = {
            "ip": ip,
            "time": now
        }


    return jsonify({
        "status": "VALID",
        "message": "License OK"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
