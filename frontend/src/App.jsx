import React, { useState, useRef, useEffect } from 'react';
import { Stage, Layer, Rect, Image as KonvaImage } from 'react-konva';
import axios from 'axios';

function App() {
    const [image, setImage] = useState(null);
    const [imageId, setImageId] = useState(null);
    const [rect, setRect] = useState(null);
    const [notes, setNotes] = useState("");
    const [uploaded, setUploaded] = useState(false);
    const [gestures, setGestures] = useState([]);
    const [selectedGestureId, setSelectedGestureId] = useState("");

    const stageRef = useRef();

    useEffect(() => {
        const fetchGestures = async () => {
            try {
                const res = await axios.get('/gestures');
                if (Array.isArray(res.data)) {
                    setGestures(res.data);
                } else {
                    console.error("Unexpected gestures response:", res.data);
                    setGestures([]);
                }
            } catch (err) {
                console.error("Failed to fetch gestures. Ensure the /gestures endpoint exists on your backend.", err);
                setGestures([]);
            }
        };
        fetchGestures();
    }, []);

    const handleFile = async (e) => {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await axios.post('/upload', formData);
            setImageId(res.data.image_id);
            const img = new window.Image();
            img.src = URL.createObjectURL(file);
            img.onload = () => setImage(img);
            setUploaded(true);
        } catch (err) {
            alert("Upload failed: " + err);
        }
    };

    const handleMouseDown = (e) => {
        if (!uploaded) return;
        const { x, y } = e.target.getStage().getPointerPosition();
        setRect({ x, y, width: 0, height: 0 });
    };

    const handleMouseMove = (e) => {
        if (!rect) return;
        const { x, y } = e.target.getStage().getPointerPosition();
        setRect(prev => ({
            ...prev,
            width: x - prev.x,
            height: y - prev.y
        }));
    };

    const handleMouseUp = () => {
        // Optional: constrain rect to positive width/height
    };

    const handleSave = async () => {
        if (!imageId || !rect) {
            alert("Please upload an image and draw a rectangle first.");
            return;
        }
        if (!selectedGestureId) {
            alert("Please select a gesture before saving.");
            return;
        }

        const payload = {
            image_id: imageId,
            gesture_id: selectedGestureId,
            region_coordinates: rect,
            notes: notes
        };

        console.log("Submitting payload:", JSON.stringify(payload));

        try {
            const res = await axios.post('/annotate', payload);
            alert("Annotation saved: " + JSON.stringify(res.data));
        } catch (err) {
            alert("Save failed: " + err);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <h2>Gesture Annotator</h2>
            <input type="file" accept="image/*" onChange={handleFile} />
            <br />
            <Stage
                width={600}
                height={400}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                ref={stageRef}
                style={{ border: '1px solid #ddd', marginTop: '10px' }}
            >
                <Layer>
                    {image && (
                        <KonvaImage
                            image={image}
                            width={600}
                            height={400}
                        />
                    )}
                    {rect && (
                        <Rect
                            x={rect.x}
                            y={rect.y}
                            width={rect.width}
                            height={rect.height}
                            stroke="red"
                            strokeWidth={2}
                        />
                    )}
                </Layer>
            </Stage>

            <textarea
                placeholder="Notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ display: 'block', marginTop: '10px', width: '600px' }}
            />

            <select
                value={selectedGestureId}
                onChange={(e) => setSelectedGestureId(e.target.value)}
                style={{ marginTop: '10px', width: '600px', padding: '5px' }}
            >
                <option value="">Select Gesture</option>
                {gestures.map((gesture) => (
                    <option key={gesture.id} value={gesture.id}>
                        {gesture.name}
                    </option>
                ))}
            </select>

            <button onClick={handleSave} style={{ marginTop: '10px' }}>
                Save Annotation
            </button>
        </div>
    );
}

export default App;
