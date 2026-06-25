from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import json
import os


from database import get_db

app = Flask(__name__)
app.secret_key = "taskworkflow_secret_key"

# # ---------- Data Storage ----------
# DATA_FILE = "tasks.json"


# def load_tasks():
#     if os.path.exists(DATA_FILE):
#         with open(DATA_FILE, "r") as f:
#             return json.load(f)
#     return []


# def save_tasks(tasks):
#     with open(DATA_FILE, "w") as f:
#         json.dump(tasks, f, indent=2)


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

    # SQL FETCH WITH USERS JOIN
    conn = get_db()

    tasks = conn.execute("""
        SELECT tasks.*,
               u1.username AS assignee_name,
               u2.username AS reviewer_name
        FROM tasks
        JOIN users u1 ON tasks.assignee_id = u1.user_id
        JOIN users u2 ON tasks.reviewer_id = u2.user_id
    """).fetchall()

    conn.close()

    tasks = [dict(task) for task in tasks]

    today = datetime.now().date()

    # Separate tasks by status
    todo_tasks = [
        t for t in tasks
        if t["assignee_name"] == current_user
        and t["status"] == "To Do"
    ]

    inprogress_tasks = [
        t for t in tasks
        if t["assignee_name"] == current_user
        and t["status"] == "In Progress"
    ]

    completed_tasks = [
        t for t in tasks
        if t["assignee_name"] == current_user
        and t["status"] == "Completed"
    ]

    assigned = todo_tasks + inprogress_tasks

    pending_review = [
        t for t in tasks
        if t["reviewer_name"] == current_user
        and t["status"] == "In Review"
    ]

    awaiting_review = []

    completed = completed_tasks

    overdue = [
        t for t in tasks
        if t["assignee_name"] == current_user
        and t["status"] != "Completed"
        and datetime.strptime(
            t["due_date"], "%Y-%m-%d"
        ).date() < today
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

    # SQL FETCH WITH USERS JOIN
    conn = get_db()

    tasks = conn.execute("""
        SELECT tasks.*,
               u1.username AS assignee_name,
               u2.username AS reviewer_name
        FROM tasks
        JOIN users u1 ON tasks.assignee_id = u1.user_id
        JOIN users u2 ON tasks.reviewer_id = u2.user_id
    """).fetchall()

    conn.close()

    tasks = [dict(task) for task in tasks]

    current_user = session["user"]

    filter_by = request.args.get("filter")
    sort_by = request.args.get("sort")
    selected_date = request.args.get("task_date")
    view = request.args.get("view", "all")

    # SHOW ONLY MY TASKS
    if view == "my":
        tasks = [
            t for t in tasks
            if t["assignee_name"] == current_user
            or t["reviewer_name"] == current_user
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

        conn = get_db()

        # CHECK ASSIGNEE
        user = conn.execute(
            "SELECT user_id FROM users WHERE username = ?",
            (assignee,)
        ).fetchone()

        if user:
            assignee_id = user["user_id"]
        else:
            conn.execute(
                "INSERT INTO users (username) VALUES (?)",
                (assignee,)
            )
            conn.commit()

            user = conn.execute(
                "SELECT user_id FROM users WHERE username = ?",
                (assignee,)
            ).fetchone()

            assignee_id = user["user_id"]

        # CHECK REVIEWER
        user = conn.execute(
            "SELECT user_id FROM users WHERE username = ?",
            (reviewer,)
        ).fetchone()

        if user:
            reviewer_id = user["user_id"]
        else:
            conn.execute(
                "INSERT INTO users (username) VALUES (?)",
                (reviewer,)
            )
            conn.commit()

            user = conn.execute(
                "SELECT user_id FROM users WHERE username = ?",
                (reviewer,)
            ).fetchone()

            reviewer_id = user["user_id"]

        # INSERT TASK
        conn.execute("""
            INSERT INTO tasks
            (
                title,
                description,
                priority,
                status,
                assignee_id,
                reviewer_id,
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
            assignee_id,
            reviewer_id,
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

    conn = get_db()

    # GET TASK FROM SQL
    task = conn.execute(
        "SELECT * FROM tasks WHERE task_id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("all_tasks"))

    # convert SQL row to dictionary
    task = dict(task)

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

    # GET CURRENT USER ID
    current_user = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (session["user"],)
    ).fetchone()

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
    if task["assignee_id"] != current_user["user_id"]:
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

    # GET CURRENT USER ID
    current_user = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (session["user"],)
    ).fetchone()

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
    if task["assignee_id"] != current_user["user_id"]:
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

    # GET CURRENT USER ID
    current_user = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (session["user"],)
    ).fetchone()

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
    if task["reviewer_id"] != current_user["user_id"]:
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

    # GET CURRENT USER ID
    current_user = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (session["user"],)
    ).fetchone()

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
    if task["reviewer_id"] != current_user["user_id"]:
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

    conn = get_db()

    # GET HISTORY FROM SQL TABLE
    history = conn.execute("""
        SELECT * FROM review_history
        WHERE task_id = ?
        ORDER BY review_id ASC
    """,
    (task_id,)
    ).fetchall()

    # GET TASK CREATED INFO
    task = conn.execute("""
        SELECT * FROM tasks
        WHERE task_id = ?
    """,
    (task_id,)
    ).fetchone()

    conn.close()

    result = []

    # ADD TASK CREATED ENTRY
    if task:
        result.append({
            "action": "Task Created",
            "assignee": task["assignee"],
            "reviewer": task["reviewer"],
            "time": task["created_date"]
        })

    # ADD HISTORY ENTRIES
    for item in history:
        result.append({
            "action": item["action"],
            "user": item["user"],
            "time": item["review_time"],
            "comment": item["comment"],
            "image": item["image"]
        })

    return jsonify(result)


@app.route("/review")
def review_tasks():

    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()

    # GET CURRENT USER ID
    current_user = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (session["user"],)
    ).fetchone()

    # GET TASKS FOR REVIEWER
    tasks = conn.execute("""
        SELECT tasks.*,
               u1.username AS assignee_name,
               u2.username AS reviewer_name
        FROM tasks
        JOIN users u1 ON tasks.assignee_id = u1.user_id
        JOIN users u2 ON tasks.reviewer_id = u2.user_id
        WHERE tasks.reviewer_id = ?
        AND tasks.status = ?
    """,
    (
        current_user["user_id"],
        "In Review"
    )).fetchall()

    conn.close()

    review_tasks_list = [dict(task) for task in tasks]

    return render_template(
        "review.html",
        tasks=review_tasks_list,
        current_user=session["user"]
    )

if __name__ == "__main__":
    app.run(debug=True)