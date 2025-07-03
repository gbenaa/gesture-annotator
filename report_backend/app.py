from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Image, GestureInstance, Gesture
import os

app = Flask(__name__)
CORS(app)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://annotator:password@localhost/gesture_db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

@app.route('/report/api/images', methods=['GET'])
def get_images():
    try:
        images = session.query(Image).all()
        data = []
        for img in images:
            gesture_instances = session.query(GestureInstance).filter_by(image_id=img.id).all()
            instances_data = []
            for inst in gesture_instances:
                gesture = session.query(Gesture).filter_by(id=inst.gesture_id).first()
                instances_data.append({
                    'id': inst.id,
                    'region_coordinates': inst.region_coordinates,
                    'notes': inst.notes,
                    'gesture': gesture.name if gesture else None,
                    'gesture_id': inst.gesture_id
                })
            data.append({
                'id': img.id,
                'filename': img.filename,
                'upload_timestamp': img.upload_timestamp.isoformat() if img.upload_timestamp else None,
                'gesture_instances': instances_data
            })
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/')
def health_check():
    return jsonify({'status': 'report backend running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
