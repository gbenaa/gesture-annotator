from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import psycopg2
import psycopg2.extras
import json
import uvicorn

with open("db_config.json", "r") as f:
    db_config = json.load(f)

app = FastAPI()
app.mount("/backend", StaticFiles(directory="/home/ubuntu/gesture-annotator-repo/backend"), name="backend")

def generate_report_data():
    conn = psycopg2.connect(dbname=db_config["dbname"], user=db_config["user"], password=db_config["password"], host="localhost", port=5432)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT gi.id AS gesture_instance_id, gi.image_id, gi.gesture_id, gi.cropped_image_path, img.filename AS image_filename, g.description AS gesture_description, gi.notes
        FROM gesture_instances gi
        JOIN images img ON img.id = gi.image_id
        LEFT JOIN gestures g ON g.id = gi.gesture_id
        ORDER BY g.description NULLS LAST;
    """)
    results = []
    for row in cur.fetchall():
        notes_text = row["notes"]
        icon_title = None
        culture_period = date_approx = place_of_creation = current_location = dimensions_mm = materials = ""
        source = location = ""
        depicted_figures = ""
        interpretation_notes = ""
        if notes_text and notes_text.strip().startswith("{"):
            try:
                notes_json = json.loads(notes_text)
                icon = notes_json.get("icon", {})
                icon_title = icon.get("title")
                culture_period = icon.get("culture_period", "")
                date_approx = icon.get("date_approx", "")
                place_of_creation = icon.get("place_of_creation", "")
                current_location = icon.get("current_location", "")
                dimensions_mm = icon.get("dimensions_mm", "")
                materials = ", ".join(icon.get("materials", []))
                image = notes_json.get("image", {})
                source = image.get("source", "")
                location = image.get("location", "")
                depicted_figures = ", ".join(notes_json.get("depicted_figures", []))
                interpretation_notes = " ".join(notes_json.get("interpretation_notes", []))
            except json.JSONDecodeError:
                pass
        results.append({
            "gesture_instance_id": row["gesture_instance_id"],
            "image_id": row["image_id"],
            "gesture_id": row["gesture_id"],
            "cropped_image_path": row["cropped_image_path"],
            "image_filename": row["image_filename"],
            "gesture_description": row["gesture_description"],
            "icon_title": icon_title,
            "culture_period": culture_period,
            "date_approx": date_approx,
            "place_of_creation": place_of_creation,
            "current_location": current_location,
            "dimensions_mm": dimensions_mm,
            "materials": materials,
            "source": source,
            "location": location,
            "depicted_figures": depicted_figures,
            "interpretation_notes": interpretation_notes
        })
    cur.close()
    conn.close()
    return results

@app.get("/report", response_class=HTMLResponse)
def report_endpoint():
    data = generate_report_data()
    data.sort(key=lambda x: (x["gesture_description"] is None, x["gesture_description"] or "", x["image_id"]))
    html_parts = [
        "<html><head><title>Gesture Instances Report</title>",
        "<style>",
        "body { font-family: sans-serif; }",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 40px; }",
        "th, td { border: 1px solid #ccc; padding: 6px; text-align: center; font-size: 14px; vertical-align: top; }",
        "th { background-color: #f2f2f2; }",
        "td.icon-title { max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }",
        "img.thumb { max-height: 180px; }",
        "img.large-icon { max-height: 300px; display: block; margin-left: 0; margin-right: auto; }",
        "img.header-img { max-height: 250px; margin: 10px 0; }",
        "h2 { margin-top: 40px; }",
        "td.left-align { text-align: left; width: 160px; }",
        "</style>",
        "</head><body>",
        "<h1>Gesture Instances Report (Grouped by Gesture Photo)</h1>"
    ]
    current_group = None
    for item in data:
        gesture_desc = item["gesture_description"] or "No Description"
        gesture_photo_path = f"/backend/gesture_photos/{item['gesture_description']}"
        if gesture_desc != current_group:
            if current_group is not None:
                html_parts.append("</table>")
            html_parts.append(f"<h2>{gesture_desc}</h2>")
            if item["gesture_description"]:
                html_parts.append(f"<img src='{gesture_photo_path}' alt='Gesture Photo' class='header-img'>")
            html_parts.append("<table>")
            html_parts.append("<tr>")
            html_parts.append("<th>Icon</th>")
            html_parts.append("<th>Gesture</th>")
            html_parts.append("<th>Icon Title</th>")
            html_parts.append("<th>Culture Period</th>")
            html_parts.append("<th>Date Approx</th>")
            html_parts.append("<th>Place of Creation</th>")
            html_parts.append("<th>Current Location</th>")
            html_parts.append("<th>Dimensions (mm)</th>")
            html_parts.append("<th>Materials</th>")
            html_parts.append("<th>Depicted Figures</th>")
            html_parts.append("<th>Source</th>")
            html_parts.append("<th>Location</th>")
            html_parts.append("<th>Interpretation Notes</th>")
            html_parts.append("<th>ID</th>")
            html_parts.append("<th>Image ID</th>")
            html_parts.append("<th>Gesture ID</th>")
            html_parts.append("<th>Image Filename</th>")
            html_parts.append("</tr>")
            current_group = gesture_desc
        cropped_img_path = f"/backend/gesture_instance_crops/{item['cropped_image_path']}"
        uploaded_img_path = f"/backend/uploads/{item['image_filename']}"
        html_parts.append("<tr>")
        html_parts.append(f"<td class='left-align'><img src='{uploaded_img_path}' alt='Icon Image' style='max-height:400px; display:block; margin-left:0; margin-right:auto;'></td>")
        html_parts.append(f"<td><img src='{cropped_img_path}' alt='Gesture Image' class='thumb'></td>")
        html_parts.append(f"<td class='icon-title'>{item['icon_title'] or 'Untitled'}</td>")
        html_parts.append(f"<td>{item['culture_period']}</td>")
        html_parts.append(f"<td>{item['date_approx']}</td>")
        html_parts.append(f"<td>{item['place_of_creation']}</td>")
        html_parts.append(f"<td>{item['current_location']}</td>")
        html_parts.append(f"<td>{item['dimensions_mm']}</td>")
        html_parts.append(f"<td>{item['materials']}</td>")
        html_parts.append(f"<td>{item['depicted_figures']}</td>")
        html_parts.append(f"<td>{item['source']}</td>")
        html_parts.append(f"<td>{item['location']}</td>")
        html_parts.append(f"<td>{item['interpretation_notes']}</td>")
        html_parts.append(f"<td>{item['gesture_instance_id']}</td>")
        html_parts.append(f"<td>{item['image_id']}</td>")
        html_parts.append(f"<td>{item['gesture_id']}</td>")
        html_parts.append(f"<td>{item['image_filename']}</td>")
        html_parts.append("</tr>")
    if current_group is not None:
        html_parts.append("</table>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
