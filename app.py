import csv
import io
from datetime import datetime
import os
import random
from flask import Flask, render_template, request, Response
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


# --- MODULE 3: ADMIN DASHBOARD & REPORTS ---
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    success_message = None

    # Allow admin to mark an unresolved complaint as Resolved
    if request.method == "POST":
        resolve_id = request.form.get("resolve_id", "").strip().upper()
        if resolve_id in complaints_db:
            complaints_db[resolve_id]["status"] = "Resolved"
            if resolve_id in schedules_db:
                schedules_db[resolve_id]["status"] = "Resolved"
            success_message = f"Complaint {resolve_id} marked as Resolved!"

    total_complaints = len(complaints_db)
    resolved_count = sum(
        1 for c in complaints_db.values() if c.get("status") == "Resolved"
    )
    unresolved_count = total_complaints - resolved_count

    # 1. Waste Category Statistics
    category_counts = {}
    for c in complaints_db.values():
        cat = c.get("category") or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    category_stats = {}
    for cat, count in category_counts.items():
        percent = round((count / total_complaints) * 100, 1) if total_complaints > 0 else 0
        category_stats[cat] = {"count": count, "percent": percent}

    # 2. Area-Wise Unresolved Issues
    area_unresolved = {}
    all_unresolved = []
    all_areas = set()

    for cid, c in complaints_db.items():
        area = c.get("location") or "Unknown Area"
        all_areas.add(area)
        if c.get("status") != "Resolved":
            item = c.copy()
            item["id"] = cid
            all_unresolved.append(item)
            area_unresolved.setdefault(area, []).append(item)

    # Filter detailed table by selected area if chosen
    selected_area = request.args.get("area", "ALL")
    if selected_area != "ALL":
        unresolved_list = [i for i in all_unresolved if i.get("location") == selected_area]
    else:
        unresolved_list = all_unresolved

    return render_template(
        "admin.html",
        total_complaints=total_complaints,
        resolved_count=resolved_count,
        unresolved_count=unresolved_count,
        category_stats=category_stats,
        area_unresolved=area_unresolved,
        unresolved_list=unresolved_list,
        all_areas=sorted(all_areas),
        selected_area=selected_area,
        success_message=success_message,
    )


@app.route("/download-report")
def download_report():
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        "Complaint ID",
        "Area / Location",
        "Waste Category",
        "Resident Name",
        "Phone",
        "Reported Date",
        "Status",
        "Description",
    ])

    # Write all complaints (with unresolved first)
    sorted_items = sorted(
        complaints_db.items(),
        key=lambda x: x[1].get("status") == "Resolved"
    )
    for cid, c in sorted_items:
        writer.writerow([
            cid,
            c.get("location", ""),
            c.get("category", ""),
            c.get("name", ""),
            c.get("phone", ""),
            c.get("date", ""),
            c.get("status", ""),
            c.get("description", ""),
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ecoclean_admin_report.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True)
