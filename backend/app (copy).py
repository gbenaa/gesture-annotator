import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from models import engine, SessionLocal, Image, GestureInstance

UPLOAD_FOLDER = os.path.expanduser('~/gesture_annotator/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ===============================
@app.route("/")
def index():
    return jsonify({"message": "Gesture Annotator Backend Running"}), 200

# ===============================
@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Save to DB
    session = SessionLocal()
    try:
        image = Image(filename=filename)
        session.add(image)
        session.commit()
        return jsonify({"message": "File uploaded", "image_id": image.id, "filename": filename}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# ===============================
@app.route("/annotate", methods=["POST"])
def annotate_gesture():
    data = request.json
    required_fields = ["image_id", "region_coordinates"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing fields, required: {required_fields}"}), 400

    image_id = data["image_id"]
    region_coordinates = data["region_coordinates"]
    notes = data.get("notes")
    gesture_id = data.get("gesture_id")

    session = SessionLocal()
    try:
        gesture_instance = GestureInstance(
            image_id=image_id,
            gesture_id=gesture_id,
            region_coordinates=region_coordinates,
            notes=notes
        )
        session.add(gesture_instance)
        session.commit()
        return jsonify({
            "message": "Annotation saved",
            "gesture_instance_id": gesture_instance.id
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
