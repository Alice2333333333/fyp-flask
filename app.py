from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

app = Flask(__name__)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Path to the JSON file in WSL
json_file_path = r"\\wsl$\Ubuntu\home\alice\fyp\data\monitor_usage.json"

# Get the data from ubuntu
@app.route("/monitor-usage", methods=["GET"])
def get_monitor_usage_data():
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)
            return data
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File not found"}), 404

# Receive asset id from flutter and insert data into firebase
@app.route('/send-assetid', methods=['POST'])
def receive_asset_id():
    try:
        request_data = request.get_json()
        assetid = request_data.get('assetid')

        if not assetid:
            return jsonify({"error": "No Asset ID provided"}), 400

        asset_doc_ref = db.collection("asset").document(assetid)
        asset_doc = asset_doc_ref.get()

        if not asset_doc.exists:
            return jsonify({"error": f"Asset ID {assetid} not found in Firestore"}), 404
        
        monitor_data = get_monitor_usage_data()
        if isinstance(monitor_data, tuple):
            return monitor_data

        subcollection_ref = asset_doc_ref.collection("usage_data")
        for item in monitor_data:
            date = item['date']
            usage_hours = item['usage_hours']

            subcollection_ref.document(date).set({
                "usage_hours": usage_hours,
            }, merge=True)

        print(f"Monitor usage data inserted into subcollection for Asset ID {assetid}")
        return jsonify({"message": f"Data for Asset ID {assetid} updated successfully"}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
