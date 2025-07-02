from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import Base, engine, SessionLocal, Image, GestureInstance
import os
from PIL import Image as PILImage
import logging

logging.basicConfig(filename='flask.log', level=logging.INFO)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
CROPS_FOLDER = os.path.join(os.getcwd(), "gesture_instance_crops")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CROPS_FOLDER, exist_ok=True)

Base.metadata.create_all(bind=engine)

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    db = SessionLocal()
    image_record = Image(filename=filename)
    db.add(image_record)
    db.commit()
    db.refresh(image_record)
    db.close()

    return jsonify({"message": "File uploaded", "image_id": image_record.id})

@app.route("/annotate", methods=["POST"])
def annotate():
    data = request.get_json()
    image_id = data.get("image_id")
    region = data.get("region_coordinates")
    notes = data.get("notes", "")

    if not image_id or not region:
        return jsonify({"error": "Missing image_id or region_coordinates"}), 400

    db = SessionLocal()
    image_record = db.query(Image).filter_by(id=image_id).first()
    if not image_record:
        db.close()
        return jsonify({"error": "Image not found"}), 404

    # Crop and save the gesture region
    try:
        image_path = os.path.join(UPLOAD_FOLDER, image_record.filename)
        img = PILImage.open(image_path)
        x, y = int(region['x']), int(region['y'])
        width, height = int(region['width']), int(region['height'])
        cropped = img.crop((x, y, x + width, y + height))

        crop_filename = f"{image_id}_{x}_{y}_{width}_{height}.png"
        crop_path = os.path.join(CROPS_FOLDER, crop_filename)
        cropped.save(crop_path)

        gesture_instance = GestureInstance(
            image_id=image_id,
            gesture_id=None,
            region_coordinates=region,
            cropped_image_path=crop_filename,
            notes=notes
        )
        db.add(gesture_instance)
        db.commit()
        db.refresh(gesture_instance)
        db.close()

        return jsonify({"message": "Annotation saved", "gesture_instance_id": gesture_instance.id})
    except Exception as e:
        db.close()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
