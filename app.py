from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import json
import os


from database import get_db

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

    # SQL FETCH

    conn = get_db()

    tasks = conn.execute(
        "SELECT * FROM tasks"
    ).fetchall()

    conn.close()

    tasks = [dict(task) for task in tasks]

    current_user = session["user"]

    filter_by = request.args.get("filter")
    sort_by = request.args.get("sort")
    selected_date = request.args.get("task_date")

    view = request.args.get("view", "all")
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

        # VALIDATION

        if not all([title, description, priority, assignee, reviewer, due_date]):
            flash("All fields are required.", "error")
            return redirect(url_for("all_tasks"))

        if assignee == reviewer:
            flash("Assignee and Reviewer cannot be the same person.", "error")
            return redirect(url_for("all_tasks"))

        # SQL INSERT (instead of JSON)

        conn = get_db()

        conn.execute("""
            INSERT INTO tasks
            (
                title,
                description,
                priority,
                status,
                assignee,
                reviewer,
                due_date,
                created_date,
                updated_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            priority,
            "To Do",
            assignee,
            reviewer,
            due_date,
            now(),
            now()
        ))

        conn.commit()
        conn.close()

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

    conn = get_db()

    # GET TASK
    task = conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?",
        (task_id,)
    ).fetchone()

    if not task:
        flash("Task not found.", "error")
        conn.close()
        return redirect(url_for("all_tasks"))

    # CHECK ASSIGNEE
    if task["assignee"] != session["user"]:
        flash("Only assignee can start task.", "error")
        conn.close()
        return redirect(url_for("all_tasks"))

    # CHECK STATUS
    if task["status"] != "To Do":
        flash("Task cannot be started now.", "error")
        conn.close()
        return redirect(url_for("all_tasks"))

    # UPDATE TASK STATUS
    conn.execute("""
        UPDATE tasks
        SET status = ?, updated_date = ?
        WHERE task_id = ?
    """,
    (
        "In Progress",
        now(),
        task_id
    ))

    # INSERT HISTORY

    conn.execute("""
        INSERT INTO review_history
        (
            task_id,
            user,
            action,
            comment,
            image,
            review_time
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        task_id,
        session["user"],
        "Started",
        "Task work started",
        "",
        now()
    ))

    conn.commit()
    conn.close()

    flash(
        f"Task '{task['title']}' is now In Progress.",
        "success"
    )

    return redirect(url_for("all_tasks"))

@app.route("/task/<int:task_id>/send_review", methods=["POST"])
def send_to_review(task_id):

    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()

    # GET TASK
    task = conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?",
        (task_id,)
    ).fetchone()

    if not task:
        flash("Task not found.", "error")
        conn.close()
        return redirect(url_for("all_tasks"))

    # CHECK ASSIGNEE
    if task["assignee"] != session["user"]:
        flash("Only assignee can send task for review.", "error")
        conn.close()
        return redirect(url_for("all_tasks"))

    # CHECK STATUS
    if task["status"] != "In Progress":
        flash("Task must be In Progress.", "error")
        conn.close()
        return redirect(url_for("all_tasks"))

    # UPDATE TASK STATUS
    conn.execute("""
        UPDATE tasks
        SET status = ?, updated_date = ?
        WHERE task_id = ?
    """,
    (
        "In Review",
        now(),
        task_id
    ))

    # INSERT HISTORY
    conn.execute("""
        INSERT INTO review_history
        (
            task_id,
            user,
            action,
            comment,
            image,
            review_time
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        task_id,
        session["user"],
        "Sent For Review",
        "Task submitted for review",
        "",
        now()
    ))

    conn.commit()
    conn.close()

    flash(
        f"Task '{task['title']}' sent for review.",
        "success"
    )

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

    conn = get_db()

    # GET TASK
    task = conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?",
        (task_id,)
    ).fetchone()

    if not task:
        flash("Task not found.", "error")
        conn.close()
        return redirect(url_for("review_tasks"))

    # CHECK REVIEWER
    if task["reviewer"] != session["user"]:
        flash("Only assigned reviewer can approve.", "error")
        conn.close()
        return redirect(url_for("review_tasks"))

    # CHECK STATUS
    if task["status"] != "In Review":
        flash("Task must be In Review.", "error")
        conn.close()
        return redirect(url_for("review_tasks"))

    # UPDATE TASK STATUS
    conn.execute("""
        UPDATE tasks
        SET status = ?, updated_date = ?
        WHERE task_id = ?
    """,
    (
        "Completed",
        now(),
        task_id
    ))

    # INSERT HISTORY
    conn.execute("""
        INSERT INTO review_history
        (
            task_id,
            user,
            action,
            comment,
            image,
            review_time
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        task_id,
        session["user"],
        "Approved",
        comment or "No comment",
        filename,
        now()
    ))

    conn.commit()
    conn.close()

    flash(
        f"Task '{task['title']}' approved and marked Completed.",
        "success"
    )

    return redirect(url_for("review_tasks"))

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

    # COMMENT REQUIRED
    if not comment:
        flash("Comment is required when rejecting task.", "error")
        return redirect(url_for("review_tasks"))

    conn = get_db()

    # GET TASK
    task = conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?",
        (task_id,)
    ).fetchone()

    if not task:
        flash("Task not found.", "error")
        conn.close()
        return redirect(url_for("review_tasks"))

    # CHECK REVIEWER
    if task["reviewer"] != session["user"]:
        flash("Only assigned reviewer can reject.", "error")
        conn.close()
        return redirect(url_for("review_tasks"))

    # CHECK STATUS
    if task["status"] != "In Review":
        flash("Task must be In Review.", "error")
        conn.close()
        return redirect(url_for("review_tasks"))

    # UPDATE STATUS
    conn.execute("""
        UPDATE tasks
        SET status = ?, updated_date = ?
        WHERE task_id = ?
    """,
    (
        "In Progress",
        now(),
        task_id
    ))

    # INSERT HISTORY
    conn.execute("""
        INSERT INTO review_history
        (
            task_id,
            user,
            action,
            comment,
            image,
            review_time
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        task_id,
        session["user"],
        "Rejected",
        comment,
        filename,
        now()
    ))

    conn.commit()
    conn.close()

    flash(
        f"Task '{task['title']}' rejected and moved back to In Progress.",
        "warning"
    )

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