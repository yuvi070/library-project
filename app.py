from flask import Flask, render_template, request, redirect, session, g, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE = "database.db"

# ------------------ DB CONNECTION ------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ------------------ INIT DB ------------------
def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        quantity INTEGER
    )
    """)

    db.commit()

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return redirect("/login")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        try:
            db.execute("INSERT INTO students(name,email,password) VALUES (?,?,?)",
                       (name, email, password))
            db.commit()
            flash("Registration Successful! Please login.")
            return redirect("/login")
        except:
            flash("Email already exists!")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # ADMIN LOGIN
        if email == "admin@gmail.com" and password == "admin":
            session["admin"] = True
            return redirect("/admin")

        db = get_db()
        user = db.execute("SELECT * FROM students WHERE email=? AND password=?",
                          (email, password)).fetchone()

        if user:
            session["user"] = user[1]
            return redirect("/dashboard")
        else:
            flash("Invalid credentials!")

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    books = db.execute("SELECT * FROM books").fetchall()

    return render_template("dashboard.html", books=books)

# ADMIN PANEL
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        quantity = request.form["quantity"]

        db.execute("INSERT INTO books(title,author,quantity) VALUES (?,?,?)",
                   (title, author, quantity))
        db.commit()
        flash("Book Added Successfully!")

    books = db.execute("SELECT * FROM books").fetchall()

    return render_template("admin.html", books=books)

# DELETE BOOK
@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    db.execute("DELETE FROM books WHERE id=?", (id,))
    db.commit()
    flash("Book Deleted!")

    return redirect("/admin")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ------------------ MAIN ------------------
if __name__ == "__main__":
    with app.app_context():
        init_db()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)