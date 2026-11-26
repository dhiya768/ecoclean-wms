from datetime import datetime
import os
import random
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder where uploaded photos will be saved
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Simple Python dictionary to store complaints
complaints_db = {}


@app.route("/", methods=["GET", "POST"])
def home():
    generated_id = None
    search_result = None
    error_message = None

    if request.method == "POST":
        action = request.form.get("action")

        # --- 1. REGISTER COMPLAINT ---
        if action == "register":
            name = request.form.get("name")
            phone = request.form.get("phone")
            location = request.form.get("location")
            category = request.form.get("category")
            description = request.form.get("description")

            # Generate unique ID
            complaint_id = f"WMS-{random.randint(1000, 9999)}"
            while complaint_id in complaints_db:
                complaint_id = f"WMS-{random.randint(1000, 9999)}"

            # Handle Photo Upload (if user attached one)
            photo_filename = None
            photo = request.files.get("photo")
            if photo and photo.filename != "":
                safe_name = secure_filename(photo.filename)
                photo_filename = f"{complaint_id}_{safe_name}"
                photo.save(
                    os.path.join(app.config["UPLOAD_FOLDER"], photo_filename)
                )

            current_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

            # Save into dictionary
            complaints_db[complaint_id] = {
                "name": name,
                "phone": phone,
                "location": location,
                "category": category,
                "description": description,
                "photo": photo_filename,
                "date": current_time,
                "status": "Pending Review",
            }
            generated_id = complaint_id

        # --- 2. SEARCH COMPLAINT ---
        elif action == "search":
            search_id = request.form.get("search_id").strip().upper()
            if search_id in complaints_db:
                search_result = complaints_db[search_id].copy()
                search_result["id"] = search_id
            else:
                error_message = (
                    f"No record found for '{search_id}'. Please check the ID"
                    " and try again."
                )

    return render_template(
        "module1.html",
        generated_id=generated_id,
        search_result=search_result,
        error_message=error_message,
        total_complaints=len(complaints_db),
    )


if __name__ == "__main__":
    app.run(debug=True)
