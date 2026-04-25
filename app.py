from flask import Flask, render_template, request, redirect, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"
DATABASE = "database.db"

# DB Connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Create Tables
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            quantity INTEGER
        )
        ''')

        db.commit()

# HOME → LOGIN
@app.route("/")
def home():
    return redirect("/login")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        db.execute("INSERT INTO students(name,email,password) VALUES (?,?,?)",
                   (name,email,password))
        db.commit()

        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM students WHERE email=? AND password=?",
                          (email,password)).fetchone()

        # ADMIN LOGIN (hardcoded simple)
        if email == "admin@gmail.com" and password == "admin":
            session["admin"] = True
            return redirect("/admin")

        if user:
            session["user"] = user[1]
            return redirect("/dashboard")
        else:
            return "Invalid Credentials"

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
@app.route("/admin", methods=["GET","POST"])
def admin():
    if "admin" not in session:
        return redirect("/login")

    db = get_db()

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        quantity = request.form["quantity"]

        db.execute("INSERT INTO books(title,author,quantity) VALUES (?,?,?)",
                   (title,author,quantity))
        db.commit()

    books = db.execute("SELECT * FROM books").fetchall()

    return render_template("admin.html", books=books)

# DELETE BOOK
@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM books WHERE id=?", (id,))
    db.commit()
    return redirect("/admin")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)