from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = "taskworkflow_secret_key"

# ---------- Data Storage ----------
DATA_FILE = "tasks.json"


def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


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

    assigned = [
        t for t in tasks
        if t["assignee"] == current_user and t["status"] != "Completed"
    ]

    pending_review = [
        t for t in tasks
        if t["reviewer"] == current_user and t["status"] == "In Review"
    ]

    awaiting_review = [
        t for t in tasks
        if t["status"] == "In Review"
    ]

    completed = [
        t for t in tasks
        if t["status"] == "Completed"
    ]

    overdue = [
        t for t in tasks
        if t["status"] != "Completed"
        and datetime.strptime(t["due_date"], "%Y-%m-%d").date() < today
    ]

    return render_template(
        "dashboard.html",
        current_user=current_user,
        assigned=assigned,
        pending_review=pending_review,
        awaiting_review=awaiting_review,
        completed=completed,
        overdue=overdue
    )


@app.route("/tasks")
def all_tasks():
    if "user" not in session:
        return redirect(url_for("index"))

    tasks = load_tasks()
    current_user = session["user"]

    # Pagination settings
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

        if not all([title, description, priority, assignee, reviewer, due_date]):
            flash("All fields are required.", "error")
            return redirect(url_for("all_tasks"))

        if assignee == reviewer:
            flash("Assignee and Reviewer cannot be the same person.", "error")
            return redirect(url_for("all_tasks"))

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

        flash(f"Task '{title}' created successfully!", "success")
        return redirect(url_for("all_tasks"))

    # no separate create_task.html anymore
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

            flash(f"Task '{task['title']}' is now In Progress.", "success")
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

            if task["assignee"] != session["user"]:
                flash("Only the assignee can send this task for review.", "error")
                break

            if task["status"] != "In Progress":
                flash("Task must be In Progress to send for review.", "error")
                break

            task["status"] = "In Review"
            task["updated_date"] = now()

            flash(f"Task '{task['title']}' sent for review.", "success")
            break

    save_tasks(tasks)
    return redirect(url_for("all_tasks"))


@app.route("/task/<int:task_id>/approve", methods=["POST"])
def approve_task(task_id):
    if "user" not in session:
        return redirect(url_for("index"))

    comment = request.form.get("comment", "").strip()
    tasks = load_tasks()

    for task in tasks:
        if task["id"] == task_id:

            if task["reviewer"] != session["user"]:
                flash("Only the assigned reviewer can approve this task.", "error")
                break

            if task["status"] != "In Review":
                flash("Task must be In Review to approve.", "error")
                break

            task["review_history"].append({
                "user": session["user"],
                "action": "Approved",
                "time": now(),
                "comment": comment or "No comment"
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

    if not comment:
        flash("A comment is required when rejecting a task.", "error")
        return redirect(url_for("review_tasks"))

    tasks = load_tasks()

    for task in tasks:
        if task["id"] == task_id:

            if task["reviewer"] != session["user"]:
                flash("Only the assigned reviewer can reject this task.", "error")
                break

            if task["status"] != "In Review":
                flash("Task must be In Review to reject.", "error")
                break

            task["review_history"].append({
                "user": session["user"],
                "action": "Rejected",
                "time": now(),
                "comment": comment
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


@app.route("/review")
def review_tasks():
    if "user" not in session:
        return redirect(url_for("index"))

    current_user = session["user"]
    tasks = load_tasks()

    my_review_tasks = [
        t for t in tasks
        if t["reviewer"] == current_user
        and t["status"] == "In Review"
    ]

    return render_template(
        "review.html",
        tasks=my_review_tasks,
        current_user=current_user
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)