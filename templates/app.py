import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-key")


def get_db():
    # opens a connection to the MySQL database
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD", ""),
        database="expense_tracker"
    )


def check_expense(amount, category, expense_date):
    # returns an error message, or None if everything is fine
    try:
        amount = float(amount)
    except ValueError:
        return "Amount must be a number."
    if amount <= 0:
        return "Amount must be greater than 0."
    if category == "" or expense_date == "":
        return "Category and date are required."
    return None


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if username == "" or len(password) < 6:
            flash("Username is required and password needs at least 6 characters.")
            return redirect(url_for("register"))

        db = get_db()
        cur = db.cursor()
        try:
            # we store the hash of the password, not the password itself
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password))
            )
            db.commit()
        except mysql.connector.IntegrityError:
            # username column is UNIQUE, so a repeated name raises this error
            cur.close()
            db.close()
            flash("That username is already taken.")
            return redirect(url_for("register"))

        cur.close()
        db.close()
        flash("Registered! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        db.close()

        if user is not None and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # all expenses of this user, newest first
    cur.execute(
        "SELECT * FROM expenses WHERE user_id = %s ORDER BY expense_date DESC",
        (session["user_id"],)
    )
    expenses = cur.fetchall()

    # total for each category in the current month
    cur.execute(
        """SELECT category, SUM(amount) AS total FROM expenses
           WHERE user_id = %s
             AND YEAR(expense_date) = YEAR(CURDATE())
             AND MONTH(expense_date) = MONTH(CURDATE())
           GROUP BY category""",
        (session["user_id"],)
    )
    summary = cur.fetchall()
    cur.close()
    db.close()

    month_total = 0
    for row in summary:
        month_total = month_total + row["total"]

    return render_template("dashboard.html", expenses=expenses,
                           summary=summary, month_total=month_total)


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"].strip()
        expense_date = request.form["expense_date"]
        note = request.form["note"].strip()

        error = check_expense(amount, category, expense_date)
        if error:
            flash(error)
            return redirect(url_for("add_expense"))

        db = get_db()
        cur = db.cursor()
        cur.execute(
            """INSERT INTO expenses (user_id, amount, category, expense_date, note)
               VALUES (%s, %s, %s, %s, %s)""",
            (session["user_id"], amount, category, expense_date, note)
        )
        db.commit()
        cur.close()
        db.close()
        return redirect(url_for("dashboard"))

    return render_template("expense_form.html", expense=None)


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # user_id is checked too, so nobody can open another user's expense
    cur.execute(
        "SELECT * FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, session["user_id"])
    )
    expense = cur.fetchone()

    if expense is None:
        cur.close()
        db.close()
        flash("Expense not found.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"].strip()
        expense_date = request.form["expense_date"]
        note = request.form["note"].strip()

        error = check_expense(amount, category, expense_date)
        if error:
            cur.close()
            db.close()
            flash(error)
            return redirect(url_for("edit_expense", expense_id=expense_id))

        cur.execute(
            """UPDATE expenses SET amount = %s, category = %s,
               expense_date = %s, note = %s
               WHERE id = %s AND user_id = %s""",
            (amount, category, expense_date, note, expense_id, session["user_id"])
        )
        db.commit()
        cur.close()
        db.close()
        return redirect(url_for("dashboard"))

    cur.close()
    db.close()
    return render_template("expense_form.html", expense=expense)


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, session["user_id"])
    )
    db.commit()
    cur.close()
    db.close()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
