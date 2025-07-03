// report_frontend/src/App.jsx – regenerated with correct image URL
import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [images, setImages] = useState([]);

  /* ------------------------------------------------------------------ */
  /* Fetch the image + gesture‑instance list from the report backend.   */
  /* ------------------------------------------------------------------ */
  useEffect(() => {
    const fetchImages = async () => {
      try {
        const res = await axios.get(
          'http://35.176.15.104:5001/report/api/images'
        );
        setImages(res.data);
      } catch (err) {
        console.error('Error fetching images:', err);
      }
    };
    fetchImages();
  }, []);

  /* Where each <img> should load from */
  const getImageUrl = (filename) =>
    `http://35.176.15.104:5001/uploads/${filename}`;

  return (
    <div style={{ padding: 20, fontFamily: 'Arial, sans-serif' }}>
      <h2>Gesture Annotator Report Viewer</h2>
      {images.length === 0 ? (
        <p>Loading images …</p>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 20,
          }}
        >
          {images.map((img) => (
            <div key={img.id} style={{ border: '1px solid #ccc', padding: 10 }}>
              <h4 style={{ fontSize: 14 }}>{img.filename}</h4>
              <img
                src={getImageUrl(img.filename)}
                alt={img.filename}
                style={{
                  width: '100%',
                  height: 'auto',
                  objectFit: 'contain',
                  background: '#f8f8f8',
                }}
                onError={(e) => {
                  e.currentTarget.src =
                    'https://via.placeholder.com/280x180?text=Not+Found';
                }}
              />

              {/* Gesture‑instance list */}
              {img.gesture_instances && img.gesture_instances.length > 0 ? (
                <div style={{ marginTop: 10 }}>
                  <h5 style={{ margin: '6px 0' }}>Gesture Instances</h5>
                  {img.gesture_instances.map((inst) => (
                    <div
                      key={inst.id}
                      style={{
                        marginBottom: 6,
                        padding: 6,
                        background: '#f9f9f9',
                        fontSize: 13,
                      }}
                    >
                      <strong>ID:</strong> {inst.id}
                      <br />
                      <strong>Gesture:</strong>{' '}
                      {inst.gesture || 'Unassigned'}
                      <br />
                      <strong>Notes:</strong> {inst.notes || 'None'}
                      <br />
                      <strong>Coords:</strong>{' '}
                      {JSON.stringify(inst.region_coordinates)}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontStyle: 'italic', color: '#666', fontSize: 13 }}>
                  No gesture instances
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
