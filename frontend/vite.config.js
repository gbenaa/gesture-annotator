import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/upload': 'http://127.0.0.1:5000',
            '/annotate': 'http://127.0.0.1:5000',
            '/gestures': 'http://127.0.0.1:5000',   // <--- Add this line if missing
        }
    }
});
