from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

# ---------- Load licenses from JSON ----------
with open("licenses.json", "r") as f:
    licenses = json.load(f)

# ---------- License check endpoint ----------
@app.route("/check_license", methods=["POST"])
def check_license_route():
    data = request.get_json()
    license_key = data.get("license")

    if license_key in licenses:
        expiry_date = datetime.datetime.strptime(licenses[license_key]["expiry"], "%Y-%m-%d")
        if datetime.datetime.now() < expiry_date:
            return jsonify({"status": "VALID", "message": "License OK"})
        else:
            return jsonify({"status": "EXPIRED", "message": "License expired"})
    else:
        return jsonify({"status": "BLOCKED", "message": "Invalid license"})

# ---------- Run server ----------
if __name__ == "__main__":
    # Локално тестирање или пристап од други компјутери
    app.run(host="0.0.0.0", port=5000)
