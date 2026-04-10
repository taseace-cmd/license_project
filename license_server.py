from flask import Flask, request, jsonify
import json
import hashlib
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

LICENSE_FILE = "licenses.json"

SERVER_SECRET = "RR_SERVER_SECRET_2026"

# runtime active sessions
active_sessions = {}


def load_licenses():
    with open(LICENSE_FILE) as f:
        return json.load(f)


def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def hash_machine(machine):
    return hashlib.sha256(machine.encode()).hexdigest()


def ip_prefix(ip):
    parts = ip.split(".")
    return ".".join(parts[:3])


def make_signature(license_key, machine_hash):
    raw = license_key + machine_hash + SERVER_SECRET
    return hashlib.sha256(raw.encode()).hexdigest()


@app.route("/check_license", methods=["POST"])
def check():

    data = request.json

    license_key = data.get("license")
    machine_id = data.get("machine_id")
    ip = data.get("ip")
    version = data.get("version")

    if version not in ["2.5", "3.0"]:
        return jsonify({
            "status": "BLOCKED",
            "message": "Version not allowed"
        })

    licenses = load_licenses()

    if license_key not in licenses:
        return jsonify({
            "status": "BLOCKED",
            "message": "Invalid license"
        })

    lic = licenses[license_key]

    expiry = datetime.datetime.strptime(
        lic["expiry"],
        "%Y-%m-%d"
    )

    if datetime.datetime.now() > expiry:
        return jsonify({
            "status": "EXPIRED"
        })

    machine_hash = hash_machine(machine_id)

    if "machines" not in lic:
        lic["machines"] = []

    machines = lic["machines"]

    # max 2 machines
    if machine_hash not in machines:

        if len(machines) >= 2:

            return jsonify({
                "status": "BLOCKED",
                "message": "Machine limit reached"
            })

        machines.append(machine_hash)

        save_licenses(licenses)

    prefix = ip_prefix(ip)

    session = active_sessions.get(license_key)

    if session:

        if session["prefix"] != prefix:

            return jsonify({
                "status": "BLOCKED",
                "message": "Different IP network"
            })

    active_sessions[license_key] = {
        "prefix": prefix,
        "time": str(datetime.datetime.now())
    }

    signature = make_signature(license_key, machine_hash)

    return jsonify({
        "status": "VALID",
        "signature": signature
    })


import os

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
