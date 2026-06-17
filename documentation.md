# Task Assignment and Review Workflow System Documentation

## Introduction

The Task Assignment and Review Workflow System is a web-based application developed using Python Flask.
The purpose of this project is to manage tasks between team members in an organized way.

In many companies, tasks are assigned to employees and after completing the work, the task goes to a reviewer for checking. This project follows the same workflow.

It helps users create tasks, assign work, review tasks, track status, and manage task history.

---

## Problem Statement

In normal task management, it becomes difficult to track who is working on a task, who is reviewing it, and whether the work is completed on time.

Without a proper workflow, tasks can be delayed and review comments may not be stored properly.

This project solves this by creating a simple workflow-based task management system.

---

## Objective

The main objectives of this project are:

* To create and assign tasks to users
* To track task progress step by step
* To allow reviewers to approve or reject tasks
* To store review comments and review history
* To monitor completed and overdue tasks
* To provide a simple dashboard for task tracking

---

## Technologies Used

### Backend

* Python
* Flask Framework

### Frontend

* HTML
* CSS
* JavaScript

### Storage

* JSON file for storing task data

### Development Tools

* Visual Studio Code
* Git
* GitHub

---

## System Workflow

Each task follows a fixed workflow.

Task Lifecycle:

To Do
↓
In Progress
↓
In Review
↓
Completed

If task is rejected:

In Review
↓
In Progress

The assignee works on the task and sends it for review.
The reviewer checks the task and either approves or rejects it.

---

## Task Attributes

Every task stores the following information:

* Task Title
* Description
* Priority (Low, Medium, High)
* Status
* Assignee
* Reviewer
* Due Date
* Created Date
* Updated Date
* Review History

---

## System Modules

### 1. Login Module

The user enters a username and logs into the system.

Purpose:

* Identify current user
* Allow task operations based on user role

---

### 2. Create Task Module

The system allows users to create tasks using a popup window.

Information entered:

* Title
* Description
* Priority
* Assignee
* Reviewer
* Due Date

Rules:

* All fields are required
* Assignee and Reviewer cannot be same person

After creation:

Task status becomes:

To Do

---

### 3. Task Management Module

After task creation, the assigned user can manage task progress.

Available actions:

Start Task

Status changes:

To Do → In Progress

Send To Review

Status changes:

In Progress → In Review

---

### 4. Review Module

The reviewer checks tasks assigned for review.

Reviewer can:

* Approve task
* Reject task
* Add review comment

Popup window is used for entering review comments.

Approve:

Status changes:

In Review → Completed

Reject:

Status changes:

In Review → In Progress

---

### 5. Review History Module

Every review action is stored.

Stored information:

* Reviewer name
* Action performed
* Date and time
* Comment

This history can be viewed inside task details page.

Example:

Rejected
Comment: Fix validation issue

Approved
Comment: Looks good now

---

### 6. Dashboard Module

Dashboard shows task summary.

It displays:

* Tasks Assigned to Me
* Tasks Pending My Review
* Tasks Awaiting Review
* Completed Tasks
* Overdue Tasks

Only limited tasks are shown to keep the dashboard clean.

---

### 7. Overdue Task Module

If task due date passes and task is not completed, it becomes overdue.

Condition:

Due Date < Current Date

AND

Task Status ≠ Completed

Overdue tasks are shown separately on dashboard.

---

### 8. Pagination Module

If too many tasks are created, the All Tasks page uses pagination.

Only 3 tasks are shown per page.

Navigation buttons:

* Previous
* Next

This improves user interface and avoids long pages.

---

## Example Workflow

Example users:

Akash → Creates task
Rahul → Assignee
Priya → Reviewer

Step 1:

Akash creates task

Status:

To Do

Step 2:

Rahul starts task

Status:

In Progress

Step 3:

Rahul sends task for review

Status:

In Review

Step 4:

Priya reviews task

Option 1:

Reject

Comment:

Fix API issue

Status:

Back to In Progress

Option 2:

Approve

Comment:

Looks good

Status:

Completed

---

## Project Structure

task-workflow/

app.py
tasks.json

templates/

login.html
dashboard.html
tasks.html
review.html
task_detail.html
base.html

static/

style.css

README.md

documentation.md

---

## Future Improvements

This project can be improved by adding:

* MySQL database
* User authentication system
* Email notifications
* Search feature
* Task filtering
* Team management

---

## Conclusion

The Task Assignment and Review Workflow System helps manage tasks in a structured and organized way.

It allows users to assign work, review tasks, track progress, and store review history.

This project demonstrates workflow management similar to real-world project management systems used in companies.
