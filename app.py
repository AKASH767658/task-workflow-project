from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = "taskworkflow_secret_key"

# ---------- Data Storage ----------

DATA_FILE = "tasks.json"
VALIDATION_FILE = "validation.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


# NEW VALIDATION FUNCTIONS

def load_validation():
    if os.path.exists(VALIDATION_FILE):
        with open(VALIDATION_FILE, "r") as f:
            return json.load(f)
    return []


def save_validation(validation_data):
    with open(VALIDATION_FILE, "w") as f:
        json.dump(validation_data, f, indent=2)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- Routes ----------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if username:
            session["user"] = username
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    current_user = session["user"]
    tasks = load_tasks()
    today = datetime.now().date()

    # Separate tasks by status (visible cards)
    todo_tasks = [
        t for t in tasks
        if t["assignee"] == current_user
        and t["status"] == "To Do"
    ]

    inprogress_tasks = [
        t for t in tasks
        if t["assignee"] == current_user
        and t["status"] == "In Progress"
    ]

    completed_tasks = [
        t for t in tasks
        if t["assignee"] == current_user
        and t["status"] == "Completed"
    ]

    # Count boxes (match visible cards)
    assigned = todo_tasks + inprogress_tasks

    pending_review = [
        t for t in tasks
        if t["reviewer"] == current_user
        and t["status"] == "In Review"
    ]

    # remove duplicate counting
    awaiting_review = []

    completed = completed_tasks

    overdue = [
        t for t in tasks
        if t["assignee"] == current_user
        and t["status"] != "Completed"
        and datetime.strptime(t["due_date"], "%Y-%m-%d").date() < today
    ]

    return render_template(
        "dashboard.html",
        current_user=current_user,
        assigned=assigned,
        pending_review=pending_review,
        awaiting_review=awaiting_review,
        completed=completed,
        overdue=overdue,
        todo_tasks=todo_tasks,
        inprogress_tasks=inprogress_tasks,
        completed_tasks=completed_tasks
    )

@app.route("/tasks")
def all_tasks():
    if "user" not in session:
        return redirect(url_for("index"))

    tasks = load_tasks()
    current_user = session["user"]

    filter_by = request.args.get("filter")
    sort_by = request.args.get("sort")
    selected_date = request.args.get("task_date")

    # NEW TOGGLE
    view = request.args.get("view", "all")

    # SHOW ONLY MY TASKS
    if view == "my":
        tasks = [
            t for t in tasks
            if t["assignee"] == current_user
            or t["reviewer"] == current_user
        ]

    # FILTER

    if filter_by == "completed":
        tasks = [
            t for t in tasks
            if t["status"] == "Completed"
        ]

    elif filter_by == "review":
        tasks = [
            t for t in tasks
            if t["status"] == "In Review"
        ]

    elif filter_by == "todo":
        tasks = [
            t for t in tasks
            if t["status"] == "To Do"
        ]

    elif filter_by == "progress":
        tasks = [
            t for t in tasks
            if t["status"] == "In Progress"
        ]

    elif filter_by == "overdue":

        today = datetime.now().date()

        tasks = [
            t for t in tasks
            if t["status"] != "Completed"
            and datetime.strptime(
                t["due_date"], "%Y-%m-%d"
            ).date() < today
        ]

    elif filter_by == "date":
        pass

    elif filter_by == "priority":

        priority_order = {
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        tasks = sorted(
            tasks,
            key=lambda x: priority_order.get(
                x["priority"], 99
            )
        )

    # SPECIFIC DATE FILTER

    if selected_date:
        tasks = [
            t for t in tasks
            if t["due_date"] == selected_date
        ]

    # SORT

    if sort_by == "newest":
        tasks = sorted(
            tasks,
            key=lambda x: x["created_date"],
            reverse=True
        )

    elif sort_by == "oldest":
        tasks = sorted(
            tasks,
            key=lambda x: x["created_date"]
        )

    # PAGINATION

    page = request.args.get("page", 1, type=int)
    per_page = 3

    start = (page - 1) * per_page
    end = start + per_page

    paginated_tasks = tasks[start:end]

    has_next = end < len(tasks)
    has_prev = page > 1

    return render_template(
        "tasks.html",
        tasks=paginated_tasks,
        current_user=current_user,
        page=page,
        has_next=has_next,
        has_prev=has_prev
    )



# FIXED FOR POPUP CREATE TASK
@app.route("/create", methods=["GET", "POST"])
def create_task():

    if "user" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "").strip()
        assignee = request.form.get("assignee", "").strip()
        reviewer = request.form.get("reviewer", "").strip()
        due_date = request.form.get("due_date", "").strip()

        # VALIDATION CHECK

        validation = {
            "title_valid": bool(title),
            "description_valid": bool(description),
            "priority_valid": bool(priority),
            "assignee_valid": bool(assignee),
            "reviewer_valid": bool(reviewer),
            "same_person_check": assignee != reviewer,
            "due_date_valid": datetime.strptime(
                due_date, "%Y-%m-%d"
            ).date() >= datetime.now().date()
        }

        # SAVE VALIDATION RESULT IN validation.json

        validation_data = load_validation()

        validation_entry = {
            "action": "Create Task",
            "time": now(),
            "validation": validation
        }

        validation_data.append(validation_entry)

        save_validation(validation_data)

        # IF VALIDATION FAILS

        if not all(validation.values()):
            flash("Validation failed. Check all fields.", "error")
            return redirect(url_for("all_tasks"))

        # CREATE TASK

        tasks = load_tasks()

        task = {
            "id": len(tasks) + 1,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "To Do",
            "assignee": assignee,
            "reviewer": reviewer,
            "due_date": due_date,
            "created_date": now(),
            "updated_date": now(),
            "review_history": []
        }

        tasks.append(task)
        save_tasks(tasks)

        flash(
            f"Task '{title}' created successfully!",
            "success"
        )

        return redirect(url_for("all_tasks"))

    return redirect(url_for("all_tasks"))


@app.route("/task/<int:task_id>")
def task_detail(task_id):
    if "user" not in session:
        return redirect(url_for("index"))

    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)

    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("all_tasks"))

    return render_template(
        "task_detail.html",
        task=task,
        current_user=session["user"]
    )


@app.route("/task/<int:task_id>/start", methods=["POST"])
def start_task(task_id):

    if "user" not in session:
        return redirect(url_for("index"))

    tasks = load_tasks()

    for task in tasks:

        if task["id"] == task_id:

            if task["assignee"] != session["user"]:
                flash("Only the assignee can start this task.", "error")
                break

            if task["status"] != "To Do":
                flash("Task cannot be started from its current status.", "error")
                break

            task["status"] = "In Progress"
            task["updated_date"] = now()

            # HISTORY SAVE
            task["review_history"].append({
                "user": session["user"],
                "action": "Started",
                "time": now(),
                "comment": "Task work started"
            })

            flash(
                f"Task '{task['title']}' is now In Progress.",
                "success"
            )
            break

    save_tasks(tasks)
    return redirect(url_for("all_tasks"))


@app.route("/task/<int:task_id>/send_review", methods=["POST"])
def send_to_review(task_id):

    if "user" not in session:
        return redirect(url_for("index"))

    tasks = load_tasks()

    for task in tasks:

        if task["id"] == task_id:

            # VALIDATION CHECK

            validation = {
                "status_check": task["status"] == "In Progress",
                "assignee_check": task["assignee"] == session["user"],
                "reviewer_present": bool(task["reviewer"])
            }

            # SAVE VALIDATION IN validation.json

            validation_data = load_validation()

            validation_entry = {
                "time": now(),
                "task_id": task_id,
                "action": "Send To Review",
                "validation": validation
            }

            validation_data.append(validation_entry)
            save_validation(validation_data)

            # IF VALIDATION FAILS

            if not all(validation.values()):
                flash("Validation failed for Send To Review.", "error")
                return redirect(url_for("all_tasks"))

            # UPDATE STATUS

            task["status"] = "In Review"
            task["updated_date"] = now()

            # HISTORY SAVE

            task["review_history"].append({
                "user": session["user"],
                "action": "Sent For Review",
                "time": now(),
                "comment": "Task submitted for review"
            })

            flash(
                f"Task '{task['title']}' sent for review.",
                "success"
            )

            break

    save_tasks(tasks)
    return redirect(url_for("all_tasks"))


@app.route("/task/<int:task_id>/approve", methods=["POST"])
def approve_task(task_id):

    if "user" not in session:
        return redirect(url_for("index"))

    comment = request.form.get("comment", "").strip()
    image = request.files.get("review_image")
    filename = ""

    if image and image.filename != "":
        filename = image.filename

        if not os.path.exists("static/uploads"):
            os.makedirs("static/uploads")

        image.save(
            os.path.join(
                "static/uploads",
                filename
            )
        )

    tasks = load_tasks()

    for task in tasks:

        if task["id"] == task_id:

            # VALIDATION CHECK

            validation = {
                "reviewer_check": task["reviewer"] == session["user"],
                "status_check": task["status"] == "In Review"
            }

            # SAVE VALIDATION IN JSON

            validation_data = load_validation()

            validation_entry = {
                "action": "Approve Task",
                "task_id": task_id,
                "time": now(),
                "validation": validation
            }

            validation_data.append(validation_entry)
            save_validation(validation_data)

            # VALIDATION FAIL

            if not all(validation.values()):
                flash("Validation failed for Approve Task.", "error")
                return redirect(url_for("review_tasks"))

            # APPROVE TASK

            task["review_history"].append({
                "user": session["user"],
                "action": "Approved",
                "time": now(),
                "comment": comment or "No comment",
                "image": filename
            })

            task["status"] = "Completed"
            task["updated_date"] = now()

            flash(
                f"Task '{task['title']}' approved and marked Completed.",
                "success"
            )

            break

    save_tasks(tasks)
    return redirect(url_for("review_tasks"))

@app.route("/task/<int:task_id>/reject", methods=["POST"])
def reject_task(task_id):

    if "user" not in session:
        return redirect(url_for("index"))

    comment = request.form.get("comment", "").strip()
    image = request.files.get("review_image")
    filename = ""

    if image and image.filename != "":
        filename = image.filename

        if not os.path.exists("static/uploads"):
            os.makedirs("static/uploads")

        image.save(
            os.path.join(
                "static/uploads",
                filename
            )
        )

    tasks = load_tasks()

    for task in tasks:

        if task["id"] == task_id:

            # VALIDATION CHECK

            validation = {
                "reviewer_check": task["reviewer"] == session["user"],
                "status_check": task["status"] == "In Review",
                "comment_check": bool(comment)
            }

            # SAVE VALIDATION

            validation_data = load_validation()

            validation_entry = {
                "action": "Reject Task",
                "task_id": task_id,
                "time": now(),
                "validation": validation
            }

            validation_data.append(validation_entry)
            save_validation(validation_data)

            # VALIDATION FAIL

            if not all(validation.values()):
                flash("Validation failed for Reject Task.", "error")
                return redirect(url_for("review_tasks"))

            # REJECT TASK

            task["review_history"].append({
                "user": session["user"],
                "action": "Rejected",
                "time": now(),
                "comment": comment,
                "image": filename
            })

            task["status"] = "In Progress"
            task["updated_date"] = now()

            flash(
                f"Task '{task['title']}' rejected and sent back to In Progress.",
                "warning"
            )

            break

    save_tasks(tasks)
    return redirect(url_for("review_tasks"))

@app.route("/history/<int:task_id>")
def get_history(task_id):

    if "user" not in session:
        return jsonify([])

    tasks = load_tasks()

    for task in tasks:

        if task["id"] == task_id:

            history = []

            # Created entry
            history.append({
                "action": "Task Created",
                "assignee": task["assignee"],
                "reviewer": task["reviewer"],
                "time": task["created_date"]
            })

            # Review entries
            if "review_history" in task:

                for item in task["review_history"]:

                    history.append({
                        "action": item["action"],
                        "user": item["user"],
                        "time": item["time"],
                        "comment": item.get("comment", ""),
                        "image": item.get("image", "")
                    })

            return jsonify(history)

    return jsonify([])


@app.route("/review")
def review_tasks():

    if "user" not in session:
        return redirect(url_for("index"))

    tasks = load_tasks()

    review_tasks_list = [

        t for t in tasks

        if t["reviewer"] == session["user"]

        and t["status"] == "In Review"
    ]

    return render_template(
        "review.html",
        tasks=review_tasks_list,
        current_user=session["user"]
    )


print(app.url_map)

if __name__ == "__main__":
    app.run(debug=True, port=5000)