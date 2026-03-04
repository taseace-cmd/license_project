from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

# Вчитување на лиценци од JSON
with open("licenses.json", "r") as f:
    licenses = json.load(f)

REQUIRED_VERSION = "2.5"

@app.route("/check_license", methods=["POST"])
def check_license():
    data = request.get_json()
    license_key = data.get("license")
    client_version = data.get("version", "")

    # Блокирај секоја стара верзија освен 2.5
    if client_version != REQUIRED_VERSION:
        return jsonify({"status": "OLD_VERSION", "message": f"Update required: {REQUIRED_VERSION} only."})

    if license_key in licenses:
        expiry_date = datetime.datetime.strptime(licenses[license_key]["expiry"], "%Y-%m-%d")
        if datetime.datetime.now() < expiry_date:
            return jsonify({"status": "VALID"})
        else:
            return jsonify({"status": "EXPIRED"})
    else:
        return jsonify({"status": "BLOCKED"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
