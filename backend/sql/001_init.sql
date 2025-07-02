BEGIN;

CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    source TEXT,
    location TEXT,
    upload_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE gestures (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE classification_systems (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE classification_system_gestures (
    id SERIAL PRIMARY KEY,
    classification_system_id INTEGER REFERENCES classification_systems(id) ON DELETE CASCADE,
    gesture_id INTEGER REFERENCES gestures(id) ON DELETE CASCADE,
    label TEXT
);

CREATE TABLE gesture_instances (
    id SERIAL PRIMARY KEY,
    image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
    gesture_id INTEGER REFERENCES gestures(id),
    region_coordinates JSONB,
    cropped_image_path TEXT,
    notes TEXT,
    embedding VECTOR(768) -- pgvector ready for CLIP embeddings
);

COMMIT;
