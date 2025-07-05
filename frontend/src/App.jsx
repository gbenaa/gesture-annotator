import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Image as KonvaImage } from 'react-konva';
import axios from 'axios';

function App() {
  const [image, setImage] = useState(null);
  const [imageId, setImageId] = useState(null);
  const [rect, setRect] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [notes, setNotes] = useState('');
  const [uploaded, setUploaded] = useState(false);
  const [gestures, setGestures] = useState([]);
  const [selectedGestureId, setSelectedGestureId] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const stageRef = useRef();

  useEffect(() => {
    const fetchGestures = async () => {
      try {
        const res = await axios.get('/gestures');
        setGestures(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error('Failed to fetch gestures:', err);
        setGestures([]);
      }
    };
    fetchGestures();
  }, []);

  const handleFile = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer ? e.dataTransfer.files[0] : e.target.files[0];
    if (!file) return;

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
      alert('Upload failed: ' + err);
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleMouseDown = (e) => {
    if (!uploaded) return;
    const { x, y } = e.target.getStage().getPointerPosition();
    setIsDrawing(true);
    setRect({ x, y, width: 0, height: 0 });
  };

  const handleMouseMove = (e) => {
    if (!isDrawing || !rect) return;
    const { x, y } = e.target.getStage().getPointerPosition();
    setRect((prev) => ({
      ...prev,
      width: x - prev.x,
      height: y - prev.y,
    }));
  };

  const handleMouseUp = () => {
    if (isDrawing) {
      setIsDrawing(false);
    }
  };

  const handleSave = async () => {
    if (!imageId || !rect) {
      alert('Please upload an image and draw a rectangle first.');
      return;
    }
    if (!selectedGestureId) {
      alert('Please select a gesture before saving.');
      return;
    }

    const payload = {
      image_id: imageId,
      gesture_id: selectedGestureId,
      region_coordinates: rect,
      notes,
    };

    try {
      const res = await axios.post('/annotate', payload);
      alert('Annotation saved: ' + JSON.stringify(res.data));

      setRect(null); // clear selection after save to allow a new annotation
      setNotes('');
      setSelectedGestureId('');
    } catch (err) {
      alert('Save failed: ' + err);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Gesture Annotator</h2>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={(e) => {
          handleFile(e);
          setDragActive(false);
        }}
        onClick={() => document.getElementById('fileInput').click()}
        style={{
          width: '600px',
          height: '120px',
          border: '3px dashed',
          borderColor: dragActive ? '#4a90e2' : '#bbb',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'border-color 0.2s',
          marginBottom: '10px',
        }}
      >
        <span style={{ color: dragActive ? '#4a90e2' : '#666' }}>
          {dragActive ? 'Drop image here…' : 'Click or drag an image here'}
        </span>
        <input
          id="fileInput"
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleFile}
        />
      </div>

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
          {image && <KonvaImage image={image} width={600} height={400} />}
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
