# Task Assignment and Review Workflow System

## Project Overview

This project is a simple task management system built using Flask and Python.
It helps users create tasks, assign tasks to team members, send tasks for review, and manage the complete workflow from start to finish.

The main goal of this project is to make task tracking easy by following a proper workflow process.

---

## Features

The project includes the following features:

* User login system
* Create task using popup window
* Assign task to one user (Assignee)
* Select reviewer for every task
* Task status management
* Review process with Approve and Reject options(reive)
* Add review comments
* Store review history
* Dashboard showing task summary
* Overdue task tracking
* Pagination for task list
* View task details and history

---

## Task Workflow

Every task follows this workflow:

To Do
↓
In Progress
↓
In Review
↓
Completed

If reviewer rejects task:

In Review
↓
Back to In Progress

---

## Task Attributes

Each task contains:

* Task Title
* Description
* Priority (Low, Medium, High)
* Status
* Assignee
* Reviewer
* Due Date
* Created Date
* Last Updated Date

---

## Reviewer Features

Reviewer can:

* View tasks assigned for review
* Add review comments
* Approve tasks
* Reject tasks
* View review history

Approve:

* Task status changes to Completed

Reject:

* Task status changes back to In Progress with comments

---

## Dashboard Features

Dashboard shows:

* Tasks Assigned to Me
* Tasks Pending My Review
* Tasks Awaiting Review
* Completed Tasks
* Overdue Tasks

To keep dashboard clean, only limited tasks are shown in preview.

---

## Technologies Used

Backend:

* Python
* Flask

Frontend:

* HTML
* CSS
* JavaScript

Data Storage:

* JSON file

Tools Used:

* VS Code
* Git
* GitHub

---

## Project Structure

```bash
task-workflow/
│
├── app.py                 # Flask application routes
├── database.py           # Database connection and table creation
├── run.py                # Single script to create DB and start project
├── task.db               # SQLite database file
├── README.md
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── tasks.html
│   ├── review.html
│   └── task_detail.html
│
├── static/
│   ├── style.css
│   └── uploads/          # Stores review images
```

```


## Task Workflow Project

How to Run Project

Step 1: Install dependencies

```bash
pip install flask
```

Step 2: Run project

```bash
python run.py
```

 What happens

* Checks if database exists
* Creates database tables if not available
* Starts Flask server automatically

Open browser

```text
http://127.0.0.1:5000
```




## Example Workflow

1. User creates task
2. Assignee starts task
3. Assignee sends task for review
4. Reviewer checks task
5. Reviewer approves or rejects task
6. Review history gets stored
7. Task gets completed after approval

---

## Future Improvements

In future this project can include:

* Database integration using MySQL
* Email notifications
* Better user authentication
* Search and filter tasks
* Team management

---

## Conclusion

This project helps manage tasks in an organized way by following a proper review workflow.

It improves task tracking, review management, and helps users monitor task progress from creation to completion.
