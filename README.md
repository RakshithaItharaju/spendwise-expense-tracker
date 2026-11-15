# SpendWise

This is a small web app I made to keep track of my daily expenses. I built it using Python (Flask) and MySQL to practice backend and database work.

## What it does

- Register and login
- Add, edit and delete expenses
- Shows the total spent this month and the total for each category
- Checks the input, so you can't add a negative amount or leave fields empty
- Each user can see only their own expenses

## Tools I used

Python, Flask, MySQL, HTML, CSS, Git

## How to run it

1. Install Python and MySQL
2. Run schema.sql in MySQL to make the database and tables
3. Run: pip install -r requirements.txt
4. Set these two values in your terminal: DB_PASSWORD (your MySQL password) and SECRET_KEY (any random text)
5. Run: python app.py
6. Open http://127.0.0.1:5000 in the browser

## What I learned

1. How a Flask app connects a web page to a Python function using routes
2. The difference between GET and POST requests
3. How to connect Python to a MySQL database and run queries
4. Why passwords should be stored as hashes and not as plain text
5. How a foreign key links two tables (one user has many expenses)
6. How to check user input so wrong data does not reach the database
