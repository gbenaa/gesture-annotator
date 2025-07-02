# Gesture Annotator

**Stack**

| Layer      | Tech |
|------------|------|
| Front-end  | React + Vite + Konva |
| Back-end   | Flask + SQLAlchemy + PostgreSQL (pgvector) |
| Dev-host   | AWS Lightsail (Ubuntu 22.04) |

## Local setup

```bash
# backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py          # runs on :5000

# frontend
cd ../frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173


