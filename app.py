from flask import Flask, render_template, request, redirect, session, g, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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

    # 🔹 STUDENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # 🔹 BOOKS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        quantity INTEGER
    )
    """)

    # 🔹 ISSUED BOOKS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issued_books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        book_id INTEGER,
        book_title TEXT,
        issue_date TEXT,
        status TEXT
    )
    """)

    # 🔥 DEFAULT BOOKS ADD (ONLY IF EMPTY)
    books_count = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    if books_count == 0:
        default_books = [
            ("Python Basics", "John", 10),
            ("Data Structures", "Mark", 8),
            ("Algorithms", "Cormen", 5),
            ("Operating System", "Galvin", 7),
            ("Computer Networks", "Tanenbaum", 6),
            ("Java Programming", "Gosling", 9),
            ("C Programming", "Dennis", 10),
            ("Web Development", "David", 6),
            ("Machine Learning", "Andrew Ng", 4),
            ("Artificial Intelligence", "Russell", 3),
            ("Software Engineering", "Sommerville", 7),
            ("Cyber Security", "Stallings", 5),
            ("Cloud Computing", "Buyya", 6),
            ("React JS", "Max", 8),
            ("Full Stack Dev", "Brad", 6),
            ("Linux Basics", "Linus", 7),
            ("Networking", "Cisco", 10),
            ("HTML CSS", "Jon", 9),
            ("JavaScript", "Kyle", 8),
            ("DBMS", "Korth", 6)
        ]

        cursor.executemany(
            "INSERT INTO books(title, author, quantity) VALUES (?, ?, ?)",
            default_books
        )

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

        # 🔥 HASH PASSWORD
        hashed_password = generate_password_hash(password)

        db = get_db()
        try:
            db.execute(
                "INSERT INTO students(name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            db.commit()
            flash("Registration Successful! Please login.")
            return redirect("/login")
        except:
            flash("Email already exists!")

    return render_template("register.html")

#RETURN BOOK
@app.route("/return/<int:id>")
def return_book(id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()

    # get record
    record = db.execute("SELECT * FROM issued_books WHERE id=?", (id,)).fetchone()

    if record and record[5] == "issued":
        # increase quantity
        db.execute("UPDATE books SET quantity = quantity + 1 WHERE id=?",
                   (record[2],))

        # update status
        db.execute("UPDATE issued_books SET status='returned' WHERE id=?", (id,))

        db.commit()
        flash("Book Returned!")

    return redirect("/dashboard")

#ISSUE

@app.route("/issue/<int:book_id>")
def issue(book_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()

    # 🔥 CHECK LIMIT (5 books max)
    count = db.execute("""
        SELECT COUNT(*) FROM issued_books 
        WHERE student_name=? AND status='issued'
    """, (session["user"],)).fetchone()[0]

    if count >= 5:
        flash("Limit reached! Max 5 books allowed.")
        return redirect("/dashboard")

    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()

    if book and book[3] > 0:
        # reduce quantity
        db.execute("UPDATE books SET quantity=? WHERE id=?",
                   (book[3] - 1, book_id))

        # insert with date
        db.execute("""
            INSERT INTO issued_books(student_name, book_id, book_title, issue_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user"],
            book_id,
            book[1],
            datetime.now().strftime("%Y-%m-%d"),
            "issued"
        ))

        db.commit()
        flash("Book Issued!")

    else:
        flash("Book not available!")

    return redirect("/dashboard")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # 🔥 ADMIN LOGIN (same as before)
        if email == "admin@gmail.com" and password == "admin":
            session["admin"] = True
            return redirect("/admin")

        db = get_db()

        # 🔥 FETCH USER BY EMAIL ONLY
        user = db.execute(
            "SELECT * FROM students WHERE email=?",
            (email,)
        ).fetchone()

        # 🔥 CHECK HASHED PASSWORD
        if user and check_password_hash(user[3], password):
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

    search = request.args.get("search")

    db = get_db()

    if search:
        books = db.execute("SELECT * FROM books WHERE title LIKE ?", 
                           ('%' + search + '%',)).fetchall()
    else:
        books = db.execute("SELECT * FROM books").fetchall()

    return render_template("dashboard.html", books=books)

# ADMIN PANEL
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/login")

    db = get_db()

    # ADD BOOK
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        quantity = request.form["quantity"]

        db.execute(
            "INSERT INTO books(title, author, quantity) VALUES (?, ?, ?)",
            (title, author, quantity)
        )
        db.commit()
        flash("Book Added Successfully!")

    # FETCH BOOKS
    books = db.execute("SELECT * FROM books").fetchall()

    # 🔥 FETCH ISSUED BOOKS (NEW)
    issued = db.execute("SELECT * FROM issued_books").fetchall()

    # PASS BOTH TO HTML
    return render_template("admin.html", books=books, issued=issued)

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