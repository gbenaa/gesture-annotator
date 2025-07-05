from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db_session, Image, GestureInstance, Gesture
from sqlalchemy.exc import SQLAlchemyError
import os
from werkzeug.utils import secure_filename
from utils import save_crop

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
CROPS_FOLDER = os.path.join(os.path.dirname(__file__), 'gesture_instance_crops')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CROPS_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        app.logger.error("No file part in request.")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        app.logger.error("Empty filename received.")
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    app.logger.info(f"File saved to {file_path}")

    new_image = Image(filename=filename, source="", location="")
    try:
        db_session.add(new_image)
        db_session.commit()
        app.logger.info(f"Image record created with id {new_image.id}")
        return jsonify({'message': 'File uploaded', 'image_id': new_image.id}), 200
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/annotate', methods=['POST'])
def annotate():
    data = request.get_json()
    if data is None:
        app.logger.error("No JSON received.")
        return jsonify({'error': 'No JSON received'}), 400

    image_id = data.get('image_id')
    gesture_id = data.get('gesture_id')
    region_coordinates = data.get('region_coordinates')
    notes = data.get('notes', '')

    if not image_id or not region_coordinates:
        app.logger.error("Missing required fields.")
        return jsonify({'error': 'Missing required fields'}), 400

    if gesture_id is not None:
        gesture = db_session.query(Gesture).filter_by(id=gesture_id).first()
        if not gesture:
            app.logger.error(f"Invalid gesture_id: {gesture_id}")
            return jsonify({'error': 'Invalid gesture_id'}), 400

    new_instance = GestureInstance(
        image_id=image_id,
        gesture_id=gesture_id,
        region_coordinates=region_coordinates,
        notes=notes,
        cropped_image_path=""
    )

    try:
        db_session.add(new_instance)
        db_session.flush()

        img = db_session.query(Image).filter_by(id=image_id).first()
        original_path = os.path.join(UPLOAD_FOLDER, img.filename)
        crop_filename = save_crop(original_path, region_coordinates, CROPS_FOLDER)

        new_instance.cropped_image_path = crop_filename
        db_session.commit()

        app.logger.info(f"Annotation saved with id {new_instance.id}, crop {crop_filename}")

        return jsonify({
            'message': 'Annotation and crop saved',
            'gesture_instance_id': new_instance.id,
            'cropped_image_path': crop_filename
        }), 200

    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"Cropping error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/gestures', methods=['GET'])
def get_gestures():
    try:
        gestures = db_session.query(Gesture).all()
        gesture_list = [
            {"id": gesture.id, "name": gesture.name, "description": gesture.description}
            for gesture in gestures
        ]
        return jsonify(gesture_list), 200
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/crops/<path:filename>')
def serve_crop(filename):
    return send_from_directory(CROPS_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
