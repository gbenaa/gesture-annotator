from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db_session, Image, GestureInstance, Gesture
from sqlalchemy.exc import SQLAlchemyError
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    if not image_id or not region_coordinates or not gesture_id:
        app.logger.error("Missing required fields.")
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate gesture_id exists
    gesture = db_session.query(Gesture).filter_by(id=gesture_id).first()
    if gesture is None:
        app.logger.error(f"Gesture with id {gesture_id} not found.")
        return jsonify({'error': 'Invalid gesture_id'}), 400

    new_instance = GestureInstance(
        image_id=image_id,
        gesture_id=gesture_id,
        region_coordinates=region_coordinates,
        cropped_image_path="",
        notes=notes
    )
    try:
        db_session.add(new_instance)
        db_session.commit()
        app.logger.info(f"Annotation saved with id {new_instance.id}")
        return jsonify({'message': 'Annotation saved', 'gesture_instance_id': new_instance.id}), 200
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
