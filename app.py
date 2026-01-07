from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "fashion_secret"

def get_db():
    return sqlite3.connect("database.db")

# ---------- DATABASE ----------
with get_db() as con:
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        image TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        total INTEGER
    )""")

    if cur.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ("Kurti",799,"p1.jpg"),("Jeans",999,"p2.jpg"),("Top",599,"p3.jpg"),
            ("Jacket",1499,"p4.jpg"),("Skirt",699,"p5.jpg"),("Saree",1299,"p6.jpg"),
            ("Dress",899,"p7.jpg"),("Tshirt",499,"p8.jpg"),("Hoodie",1199,"p9.jpg"),
            ("Palazzo",799,"p10.jpg"),("Blazer",1599,"p11.jpg"),
            ("Shorts",499,"p12.jpg"),("Gown",1999,"p13.jpg"),
            ("Shrug",699,"p14.jpg"),("Denim Shirt",899,"p15.jpg")
        ]
        cur.executemany("INSERT INTO products(name,price,image) VALUES(?,?,?)",products)
    con.commit()

# ---------- ROUTES ----------
@app.route("/")
def index():
    con = get_db()
    products = con.execute("SELECT * FROM products").fetchall()
    return render_template("index.html", products=products)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        con = get_db()
        con.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)",
                    (request.form["username"],
                     generate_password_hash(request.form["password"]),
                     "user"))
        con.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = get_db()
        user = con.execute("SELECT * FROM users WHERE username=?",
                           (request.form["username"],)).fetchone()
        if user and check_password_hash(user[2],request.form["password"]):
            session["user"] = user[1]
            session["role"] = user[3]
            session["cart"] = []
            return redirect("/")
    return render_template("login.html")

@app.route("/add/<int:id>")
def add_cart(id):
    session["cart"].append(id)
    return redirect("/")

@app.route("/remove/<int:id>")
def remove_cart(id):
    session["cart"].remove(id)
    return redirect("/cart")

@app.route("/cart")
def cart():
    con = get_db()
    items = []
    total = 0
    for pid in session.get("cart",[]):
        p = con.execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
        items.append(p)
        total += p[2]
    return render_template("cart.html", items=items, total=total)

@app.route("/pay")
def pay():
    total = 0
    con = get_db()
    for pid in session["cart"]:
        total += con.execute("SELECT price FROM products WHERE id=?",(pid,)).fetchone()[0]
    con.execute("INSERT INTO orders(user,total) VALUES(?,?)",(session["user"],total))
    con.commit()
    session["cart"]=[]
    return "<h2>Payment Successful ✔</h2>"

@app.route("/admin", methods=["GET","POST"])
def admin():
    if session.get("role")!="admin":
        return redirect("/")
    con = get_db()
    if request.method=="POST":
        con.execute("INSERT INTO products(name,price,image) VALUES(?,?,?)",
                    (request.form["name"],request.form["price"],request.form["image"]))
        con.commit()
    products = con.execute("SELECT * FROM products").fetchall()
    orders = con.execute("SELECT * FROM orders").fetchall()
    return render_template("admin.html", products=products, orders=orders)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
