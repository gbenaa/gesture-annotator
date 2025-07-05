"""
 backend/app.py – full, self‑contained Flask application
 =====================================================
 • Preserves existing upload → annotate workflow.
 • Adds JSON metadata ingestion via the *notes* field.
 • Updates/creates Image, Icon, IconImage and IconInscription records when
   valid JSON is detected.
 • Uses the legacy global ``db_session`` for continuity; refactor to context
   managers later if desired.
 • British English comments, no emojis.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from models import SessionLocal, Image, GestureInstance, Gesture, Icon, IconImage, IconInscription

from utils import save_crop

db_session = SessionLocal()

# ---------------------------------------------------------------------------
# Flask app initialisation
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

ROOT_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = ROOT_DIR / "uploads"
CROPS_FOLDER = ROOT_DIR / "gesture_instance_crops"
UPLOAD_FOLDER.mkdir(exist_ok=True)
CROPS_FOLDER.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Helper – process pasted metadata JSON from the notes field
# ---------------------------------------------------------------------------

def _process_metadata(meta: Dict[str, Any], image: Image) -> None:  # noqa: D401
    """Populate ancillary tables from metadata JSON.

    -> *meta* is the dict parsed from the notes field.
    -> *image* is the Image ORM instance already persisted.
    """

    # ------------------------- Image level updates ------------------------
    img_meta = meta.get("image", {})
    if img_meta:
        image.source = img_meta.get("source", image.source)
        image.location = img_meta.get("location", image.location)

    # --------------------------- Icon handling ----------------------------
    icon_meta = meta.get("icon")
    if not icon_meta:
        db_session.flush()
        return  # nothing further to do

    # Create Icon record
    icon = Icon(
        iconographic_variant_id=icon_meta.get("iconographic_variant_id"),
        title=icon_meta.get("title"),
        object_type=icon_meta.get("object_type", "icon"),
        museum_collection_number=icon_meta.get("museum_collection_number"),
        culture_period=icon_meta.get("culture_period"),
        date_approx=icon_meta.get("date_approx"),
        place_of_creation=icon_meta.get("place_of_creation"),
        current_location=icon_meta.get("current_location"),
        acquisition_method=icon_meta.get("acquisition_method"),
        acquisition_source=icon_meta.get("acquisition_source"),
        acquisition_date=icon_meta.get("acquisition_date"),
        materials=icon_meta.get("materials"),
        techniques=icon_meta.get("techniques"),
        dimensions_mm=icon_meta.get("dimensions_mm"),
        image_url=icon_meta.get("image_url"),
        condition_report=icon_meta.get("condition_report"),
    )
    db_session.add(icon)
    db_session.flush()  # obtain icon.id

    # ------------------------- Single icon image -------------------------
    icon_image_meta = meta.get("icon_image")
    if icon_image_meta:
        db_session.add(
            IconImage(
                icon_id=icon.id,
                image_url=icon_image_meta.get("image_url"),
                photographer=icon_image_meta.get("photographer"),
                copyright_holder=icon_image_meta.get("copyright_holder"),
                date_taken=icon_image_meta.get("date_taken"),
                resolution=icon_image_meta.get("resolution"),
                lighting_notes=icon_image_meta.get("lighting_notes"),
            )
        )

    # ------------------------ Icon inscriptions --------------------------
    inscriptions_meta: List[Dict[str, Any]] = meta.get("icon_inscriptions", [])
    for ins in inscriptions_meta:
        db_session.add(
            IconInscription(
                icon_id=icon.id,
                language=ins.get("language"),
                text=ins.get("text"),
                location_on_icon=ins.get("location_on_icon"),
                script_type=ins.get("script_type"),
                translation=ins.get("translation"),
            )
        )

    db_session.flush()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        app.logger.error("No file part in request.")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        app.logger.error("Empty filename received.")
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    file_path = UPLOAD_FOLDER / filename
    file.save(file_path)
    app.logger.info(f"File saved to {file_path}")

    new_image = Image(filename=filename, source="", location="")
    try:
        db_session.add(new_image)
        db_session.commit()
        app.logger.info(f"Image record created with id {new_image.id}")
        return jsonify({"message": "File uploaded", "image_id": new_image.id}), 200
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/annotate", methods=["POST"])
def annotate():
    data = request.get_json()
    if data is None:
        app.logger.error("No JSON received.")
        return jsonify({"error": "No JSON received"}), 400

    image_id = data.get("image_id")
    gesture_id = data.get("gesture_id")
    region_coordinates = data.get("region_coordinates")
    notes = data.get("notes", "")

    if not image_id or not region_coordinates:
        app.logger.error("Missing required fields.")
        return jsonify({"error": "Missing required fields"}), 400

    # Validate gesture id (if provided)
    if gesture_id is not None:
        gesture = db_session.query(Gesture).filter_by(id=gesture_id).first()
        if not gesture:
            app.logger.error(f"Invalid gesture_id: {gesture_id}")
            return jsonify({"error": "Invalid gesture_id"}), 400

    # Create gesture instance (without crop yet)
    new_instance = GestureInstance(
        image_id=image_id,
        gesture_id=gesture_id,
        region_coordinates=region_coordinates,
        notes=notes,
        cropped_image_path="",
    )

    try:
        db_session.add(new_instance)
        db_session.flush()  # ensure new_instance.id available

        # Perform cropping and save path
        img = db_session.query(Image).filter_by(id=image_id).first()
        original_path = UPLOAD_FOLDER / img.filename
        crop_filename = save_crop(original_path, region_coordinates, CROPS_FOLDER)
        new_instance.cropped_image_path = crop_filename

        # ---------------- Parse metadata JSON in notes -----------------
        meta_dict: Dict[str, Any] | None = None
        try:
            meta_dict = json.loads(notes) if notes.strip().startswith("{") else None
        except json.JSONDecodeError:
            meta_dict = None  # leave notes as plain text

        if meta_dict:
            _process_metadata(meta_dict, img)

        db_session.commit()
        app.logger.info(
            f"Annotation saved id={new_instance.id}, crop={crop_filename}"
        )

        return (
            jsonify(
                {
                    "message": "Annotation and metadata saved",
                    "gesture_instance_id": new_instance.id,
                    "cropped_image_path": crop_filename,
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        db_session.rollback()
        app.logger.error(f"Processing error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/gestures", methods=["GET"])
def get_gestures():
    try:
        gestures = db_session.query(Gesture).all()
        return (
            jsonify(
                [
                    {
                        "id": g.id,
                        "name": g.name,
                        "description": g.description,
                    }
                    for g in gestures
                ]
            ),
            200,
        )
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/crops/<path:filename>")
def serve_crop(filename: str):
    return send_from_directory(CROPS_FOLDER, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
