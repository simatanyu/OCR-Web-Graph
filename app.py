from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
import os
import csv
import subprocess

app = Flask(__name__, static_folder='static', template_folder='templates')

DOWNLOAD_FOLDER = os.path.join(app.root_path, 'static', 'Websitematerial')
UPLOAD_FOLDER = "uploads"
IMAGE_FOLDER = os.path.join(app.root_path, "uploads", "Image")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# May 15, The name of upload folder and local store csv should have different name
csv_path = os.path.join(UPLOAD_FOLDER, "Extracted_Numbers.csv")

# Check existence of csv
if not os.path.exists(csv_path):
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Value"])  # CSV reader

# Main render
@app.route("/")
def index():

    return render_template("index.html")

# API Obtain data from raspberry PI
@app.route('/realtime_data')
def get_realtime_data():
    try:
        df = pd.read_csv(csv_path)
        return jsonify([
            {"timestamp": row["timestamp"], "value": row["value"]}
            for _, row in df.iterrows()
        ])
    except FileNotFoundError:
        return jsonify([])  # Error Exception
    except Exception as e:
        return jsonify({"error": str(e)})

# API: Upload
@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    """Upload data"""
    data = request.json
    print ("Receving data:", data)
    if not data or "timestamp" not in data or "value" not in data:
        return jsonify({"error": "Invalid data"}), 400

    #CSV Recorder
    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([data["timestamp"], data["value"]])

    print(f"Data saved: {data['timestamp']} - {data['value']}")
    return jsonify({"message": "CSV Upload Success"}), 200

# API: Delete Old Graph
@app.route('/delete_data', methods=['POST'])
def delete_data():
    try:
        if os.path.exists(csv_path):
            os.remove(csv_path) # Delete
            with open(csv_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Value"]) # Recreate path
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "file_not_found"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
            
# API: CSV Download Option
# May 15: This function need test and update
@app.route("/download_history/<filename>")
def download_history(filename):
    """Download Option"""
    history_dir = os.path.join(UPLOAD_FOLDER, "history")
    return send_from_directory(history_dir, filename, as_attachment=True)

# List history csv on website
@app.route('/list_history')
def list_history():
    try:
        files = os.listdir("history/data")
        csv_files = [f for f in files if f.endswith('.csv')]
        csv_files.sort(reverse=True)
        return jsonify(csv_files)
    except Exception as e:
        return jsonify({"error": str(e)})

# Read history CSV file from Data directory
@app.route('/load_history_data/<filename>')
def load_history_data(filename):
    filepath = os.path.join('history/data', filename)
    try:
        df = pd.read_csv(filepath, parse_dates=["timestamp"], dtype={"value": float})
        # Process abnormal value
        df['value'] = pd.to_numeric(df['value'].astype(str), errors='coerce')
        df = df.dropna(subset=['value'])

        if df.empty or 'timestamp' not in df.columns or 'value' not in df.columns:
            return jsonify([])
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)})

# Save current data table
@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        data = request.json
        df = pd.DataFrame(data)
        now = datetime.now()
        filename = f"{now.strftime('%Y-%m-%d_%H-%M')}.csv" # May 16, fixed double save
        filepath = os.path.join('history/data/', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)
        return jsonify({"status": "success", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/image_list')
def image_list():
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg'))]
    files.sort()
    return jsonify(files)

@app.route('/uploads/Image/<path:filename>')
def get_image(filename):
    return send_from_directory('uploads/Image', filename)

@app.route('/start_ocr', methods=['POST'])
def start_ocr():
    try:
        subprocess.Popen([
            "python3",
            "/home/pi/PycharmProject/OCR-Wab/Integrate-1_May_30.py"
        ])
        return jsonify({"status": "success", "message": "OCR Start"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return "404 - Not Found", 404

@app.errorhandler(403)
def forbidden(e):
    return "403 - Forbidden", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
