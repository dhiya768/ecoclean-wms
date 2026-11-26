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

schedules_db = {}

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


@app.route('/schedules', methods=['GET', 'POST'])
def schedules():
    success_message = None
    error_message = None
    schedule_result = None

    if request.method == 'POST':
        action = request.form.get('action')

        # 1. Assign a pickup date to an existing Complaint ID
        if action == 'schedule_pickup':
            cid = request.form.get('complaint_id', '').strip().upper()

            # Check if the Complaint ID actually exists in Module 1's complaints!
            if cid not in complaints_db:
                error_message = f"Complaint ID '{cid}' not found. Please register the complaint first."
            else:
                schedules_db[cid] = {
                    'complaint_id': cid,
                    'location': complaints_db[cid]['location'],
                    'category': complaints_db[cid]['category'],
                    'pickup_date': request.form.get('pickup_date'),
                    'time_slot': request.form.get('time_slot'),
                    'vehicle_no': request.form.get('vehicle_no'),
                    'status': 'Pickup Scheduled'
                }
                # Also update the complaint's status in Module 1!
                complaints_db[cid]['status'] = 'Pickup Scheduled'
                success_message = f"Pickup scheduled for {cid} on {request.form.get('pickup_date')}!"

        # 2. Search scheduled pickup date by Complaint ID
        elif action == 'check_schedule':
            search_id = request.form.get('search_id', '').strip().upper()
            if search_id in schedules_db:
                schedule_result = schedules_db[search_id]
            elif search_id in complaints_db:
                error_message = f"Complaint '{search_id}' is registered, but no pickup date has been scheduled yet."
            else:
                error_message = f"No complaint found with ID '{search_id}'."

    return render_template(
        'schedules.html',
        total_complaints=len(complaints_db),
        success_message=success_message,
        error_message=error_message,
        schedule_result=schedule_result
    )






if __name__ == "__main__":
    app.run(debug=True)
