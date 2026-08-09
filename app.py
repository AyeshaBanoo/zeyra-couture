from flask import Flask, render_template, redirect, request,session,flash
import os
print(os.path.abspath("database.db"))
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection,get_all_products
app=Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "ayeshuu137@gmail.com"
app.config["MAIL_PASSWORD"] = "yfjv fzwb jwxy gxxw"

mail = Mail(app)

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
app.secret_key = os.environ.get("SECRET_KEY")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/products")
def products_page():

    search = request.args.get("search", "")

    conn = get_connection()

    if search:

        products = conn.execute(
            """
            SELECT
                products.id,
                products.name,
                products.price,
                products.description,
                colors.image
            FROM products
            LEFT JOIN colors
            ON products.id = colors.product_id
            WHERE products.name LIKE ?
            GROUP BY products.id
            """,
            ("%" + search + "%",)
        ).fetchall()

    else:

        products = conn.execute(
            """
            SELECT
                products.id,
                products.name,
                products.price,
                products.description,
                colors.image
            FROM products
            LEFT JOIN colors
            ON products.id = colors.product_id
            GROUP BY products.id
            """
        ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products
    )
@app.route("/product/<int:id>")
def product(id):

    conn = get_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    colors = conn.execute(
        """
        SELECT *
        FROM colors
        WHERE product_id = ?
        """,
        (id,)
    ).fetchall()

    sizes = conn.execute(
        """
        SELECT *
        FROM sizes
        WHERE product_id = ?
        """,
        (id,)
    ).fetchall()

    conn.close()

    return render_template(
        "product.html",
        product=product,
        colors=colors,
        sizes=sizes
    )
@app.route("/add_to_cart/<int:id>", methods=["POST"])
def add_to_cart(id):

    if "user" not in session:
        return redirect("/login")

    selected_size = request.form["size"]
    selected_color = request.form["color"]

    conn = get_connection()

    product = conn.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    color = conn.execute(
        """
        SELECT *
        FROM colors
        WHERE product_id = ?
        AND color_name = ?
        """,
        (id, selected_color)
    ).fetchone()

    if product is None:
        conn.close()
        flash("❌ Product not found!")
        return redirect("/products")

    selected_image = ""

    if color:
        selected_image = color["image"]

    existing = conn.execute(
        """
        SELECT *
        FROM cart
        WHERE
        user_email = ?
        AND product_id = ?
        AND size = ?
        AND color = ?
        """,
        (
            session["user"]["email"],
            id,
            selected_size,
            selected_color
        )
    ).fetchone()

    if existing:

        conn.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE id = ?
            """,
            (existing["id"],)
        )

    else:

        conn.execute(
            """
            INSERT INTO cart
            (
                user_email,
                product_id,
                product_name,
                color,
                size,
                quantity,
                price,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user"]["email"],
                product["id"],
                product["name"],
                selected_color,
                selected_size,
                1,
                product["price"],
                selected_image
            )
        )

    conn.commit()
    conn.close()

    flash("✅ Added to cart!")

    return redirect("/cart")
@app.route("/cart")
def cart_page():

    if "user" not in session:
        return redirect("/login")

    conn = get_connection()

    cart = conn.execute(
        """
        SELECT *
        FROM cart
        WHERE user_email = ?
        """,
        (session["user"]["email"],)
    ).fetchall()

    total = 0

    for item in cart:
        total += item["price"] * item["quantity"]

    conn.close()

    return render_template(
        "cart.html",
        cart=cart,
        total=total
    )
@app.route("/increase_quantity/<int:id>")
def increase_quantity(id):

    if "user" not in session:
        return redirect("/login")

    conn = get_connection()

    conn.execute(
        """
        UPDATE cart
        SET quantity = quantity + 1
        WHERE id = ?
        AND user_email = ?
        """,
        (
            id,
            session["user"]["email"]
        )
    )

    conn.commit()
    conn.close()

    return redirect("/cart")
@app.route("/decrease_quantity/<int:id>")
def decrease_quantity(id):

    if "user" not in session:
        return redirect("/login")

    conn = get_connection()

    item = conn.execute(
        """
        SELECT quantity
        FROM cart
        WHERE id = ?
        AND user_email = ?
        """,
        (
            id,
            session["user"]["email"]
        )
    ).fetchone()

    if item:

        if item["quantity"] > 1:

            conn.execute(
                """
                UPDATE cart
                SET quantity = quantity - 1
                WHERE id = ?
                AND user_email = ?
                """,
                (
                    id,
                    session["user"]["email"]
                )
            )

        else:

            conn.execute(
                """
                DELETE FROM cart
                WHERE id = ?
                AND user_email = ?
                """,
                (
                    id,
                    session["user"]["email"]
                )
            )

    conn.commit()
    conn.close()

    return redirect("/cart")
@app.route("/remove_from_cart/<int:id>")
def remove_from_cart(id):

    if "user" not in session:
        return redirect("/login")

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM cart
        WHERE id = ?
        AND user_email = ?
        """,
        (
            id,
            session["user"]["email"]
        )
    )

    conn.commit()
    conn.close()

    flash("🗑 Product removed from cart!")

    return redirect("/cart")
@app.route("/request_order")
def request_order():
    if "user" not in session:
        return redirect("/login")
    return render_template("request_order.html")
@app.route("/order_summary", methods=["POST"])
def order_summary():

    if "user" not in session:
        return redirect("/login")


    name = request.form["name"]
    phone = request.form["phone"]
    address = request.form["address"]
    pincode = request.form["pincode"]

    conn = get_connection()

    cart = conn.execute(
        """
        SELECT *
        FROM cart
        WHERE user_email = ?
        """,
        (session["user"]["email"],)
    ).fetchall()

    total = 0
    delivery = 80

    for item in cart:
        total += item["price"] * item["quantity"]

    grand_total = total + delivery

    from datetime import datetime

    current_date = datetime.now().strftime("%d-%m-%Y")
    current_time = datetime.now().strftime("%I:%M %p")

    cursor = conn.execute(
        """
        INSERT INTO orders
        (
            customer_name,
            email,
            phone,
            address,
            pincode,
            total,
            status,
            payment,
            date,
            time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            session["user"]["email"],
            phone,
            address,
            pincode,
            grand_total,
            "Order Received",
            "Pending",
            current_date,
            current_time
        )
    )

    # SQLite-generated unique ID
    order_db_id = cursor.lastrowid

    # Customer-facing order ID
    order_id = f"ZYC{order_db_id}"

    # Save ZYC order ID into orders table
    conn.execute(
        """
        UPDATE orders
        SET order_id = ?
        WHERE id = ?
        """,
        (order_id, order_db_id)
    )


    for item in cart:

        conn.execute(
            """
            INSERT INTO order_items
            (
                order_id,
                product_name,
                color,
                size,
                quantity,
                price,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["product_name"],
                item["color"],
                item["size"],
                item["quantity"],
                item["price"],
                item["image"]
            )
        )


    session["last_order"] = {
        "order_id": order_id,
        "name": name,
        "phone": phone,
        "email": session["user"]["email"],
        "address": address,
        "pincode": pincode,
        "grand_total": grand_total,
        "cart": [dict(item) for item in cart]
    }

  
    conn.execute(
        """
        DELETE FROM cart
        WHERE user_email = ?
        """,
        (session["user"]["email"],)
    )

    conn.commit()
    conn.close()

    flash("✅ Order placed successfully!")

   
    return render_template(
        "order_summary.html",
        order_id=order_id,
        name=name,
        phone=phone,
        address=address,
        pincode=pincode,
        cart=cart,
        total=total,
        grand_total=grand_total
    )
@app.route("/admin_orders")
def admin_orders():
    if not session.get("admin"):
        return redirect("/admin/login")

    search = request.args.get("search", "")

    conn = get_connection()

    if search:

        order_rows = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE
            customer_name LIKE ?
            OR phone LIKE ?
            OR order_id LIKE ?
            ORDER BY id DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        order_rows = conn.execute(
            """
            SELECT *
            FROM orders
            ORDER BY id DESC
            """
        ).fetchall()

    orders = []

    for order in order_rows:

        order = dict(order)

        items = conn.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = ?
            """,
            (order["order_id"],)
        ).fetchall()

        order["items"] = [dict(item) for item in items]

        orders.append(order)

    conn.close()
    return render_template(
        "admin_orders.html",
        orders=orders,
        search=search
    )
@app.route("/payment")
def payment():
    total = orders[-1]["total"]
    return render_template(
        "payment.html",
        total=total
    )
@app.route("/order_success", methods=["POST"])
def order_success():

    order = session.get("last_order")

    if order:

        items_text = ""

        for item in order["cart"]:
            items_text += (
                f"{item['product_name']}\n"
                f"Color: {item['color']}\n"
                f"Size: {item['size']}\n"
                f"Quantity: {item['quantity']}\n"
                f"Price: ₹{item['price']}\n\n"
            )

        msg = Message(
            subject=f"🛍️ New Order - {order['order_id']}",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]]
        )

        msg.body = f"""
New Order Received

Order ID: {order['order_id']}

Customer: {order['name']}
Email: {order['email']}
Phone: {order['phone']}

Address:
{order['address']}

Pincode:
{order['pincode']}

Products:

{items_text}

Grand Total: ₹{order['grand_total']}
"""

        mail.send(msg)

        # Prevent duplicate emails if user refreshes
        session.pop("last_order", None)

    flash("🎉 Order placed successfully!")

    return render_template("order_success.html")
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (session["user"]["email"],)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )
@app.route("/my_orders")
def my_orders():

    if "user" not in session:
        return redirect("/login")

    conn = get_connection()

    order_rows = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE email = ?
        ORDER BY id DESC
        """,
        (session["user"]["email"],)
    ).fetchall()

    orders = []

    for order in order_rows:

        order = dict(order)

        items = conn.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = ?
            """,
            (order["order_id"],)
        ).fetchall()

        order["items"] = items

        orders.append(order)

    conn.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        conn = get_connection()

        conn.execute(
            """
            UPDATE users
            SET
                name = ?,
                phone = ?,
                address = ?,
                pincode = ?
            WHERE email = ?
            """,
            (
                request.form["name"],
                request.form["phone"],
                request.form["address"],
                request.form["pincode"],
                session["user"]["email"]
            )
        )

        conn.commit()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (session["user"]["email"],)
        ).fetchone()

        conn.close()

        session["user"] = dict(user)

        flash("✅ Profile updated successfully!")

        return redirect("/profile")

    return render_template(
        "edit_profile.html",
        user=session["user"]
    )
@app.route("/register", methods=["GET", "POST"])  
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = generate_password_hash(request.form["password"])
        address = request.form["address"]
        pincode = request.form["pincode"]

        user = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
             "address": address,
             "pincode": pincode
        }

        from db import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users
        (name, email, phone, password, address, pincode)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            password,
            address,
            pincode
        ))

        conn.commit()
        conn.close()
        return redirect("/login")
    
    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        # Check the entered password against the stored hash
        if user and check_password_hash(user["password"], password):

            session["user"] = dict(user)

            flash("✅ Logged in successfully!")

            return redirect("/")

        else:

            flash("❌ Invalid Email or Password!")

            return redirect("/login")

    return render_template("login.html")
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin/login")
    return render_template("admin.html")
@app.route("/admin/products")
def admin_products():
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_connection()

    products = conn.execute("""
        SELECT
            products.id,
            products.name,
            products.price,
            products.description,
            colors.id AS color_id,
            colors.color_name,
            colors.image
        FROM products
        LEFT JOIN colors
        ON products.id = colors.product_id
        GROUP BY products.id
    """).fetchall()

    conn.close()

    return render_template(
        "admin_products.html",
        products=products
    )
@app.route("/admin/add_product", methods=["GET", "POST"])
def add_product():
    if not session.get("admin"):
        return redirect("/admin/login")

    if request.method == "POST":

        print("POST RECEIVED")

        name = request.form["name"]
        price = int(request.form["price"])
        description = request.form["description"]

        image = request.files["image"]

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        color = request.form["color"]
        sizes = request.form.getlist("sizes")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO products (name, price, description)
        VALUES (?, ?, ?)
        """, (name, price, description))

        product_id = cursor.lastrowid

        # Insert first color
        cursor.execute("""
        INSERT INTO colors (product_id, color_name, image)
        VALUES (?, ?, ?)
        """, (product_id, color, filename))

        # Insert sizes
        for size in sizes:
            cursor.execute("""
            INSERT INTO sizes (product_id, size)
            VALUES (?, ?)
            """, (product_id, size))

        conn.commit()
        conn.close()

        print("PRODUCT SAVED TO DATABASE")
        
        return redirect("/admin/products")

    return render_template("add_product.html")
    
   
@app.route("/admin/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_connection()

    if request.method == "POST":

        conn.execute(
            """
            UPDATE products
            SET
                name = ?,
                price = ?,
                description = ?
            WHERE id = ?
            """,
            (
                request.form["name"],
                int(request.form["price"]),
                request.form["description"],
                id
            )
        )

        conn.commit()

        conn.execute(
            "DELETE FROM sizes WHERE product_id = ?",
            (id,)
        )

        sizes = request.form.getlist("sizes")

        for size in sizes:

            conn.execute(
                """
                INSERT INTO sizes(product_id,size)
                VALUES(?,?)
                """,
                (id, size)
            )

        conn.commit()

        conn.close()

        flash("✅ Product updated successfully!")

        return redirect("/admin/products")

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (id,)
    ).fetchone()

    colors = conn.execute(
        "SELECT * FROM colors WHERE product_id = ?",
        (id,)
    ).fetchall()

    sizes = conn.execute(
        "SELECT * FROM sizes WHERE product_id = ?",
        (id,)
    ).fetchall()

    conn.close()

    return render_template(
        "edit_product.html",
        product=product,
        colors=colors,
        sizes=sizes
    )
@app.route("/admin/delete_product/<int:id>")
def delete_product(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_connection()

    conn.execute(
        "DELETE FROM colors WHERE product_id = ?",
        (id,)
    )
    conn.execute(
        "DELETE FROM sizes WHERE product_id = ?",
        (id,)
    )
    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (id,)
    )

    conn.commit()

    conn.close()

    flash("🗑 Product deleted successfully!")

    return redirect("/admin/products")
@app.route("/logout")
def logout():

    session.pop("user", None)
    flash("👋 Logged out successfully!")

    return redirect("/login")
@app.route("/add_color/<int:id>", methods=["GET", "POST"])
def add_color(id):
    if not session.get("admin"):
        return redirect("/admin/login")
    conn = get_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (id,)
    ).fetchone()

    if product is None:
        conn.close()
        return "Product not found"

    if request.method == "POST":

        color_name = request.form["color"]

        image = request.files["image"]

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        conn.execute(
            """
            INSERT INTO colors(product_id, color_name, image)
            VALUES(?, ?, ?)
            """,
            (id, color_name, filename)
        )

        conn.commit()

        conn.close()

        flash("✅ New color added successfully!")

        return redirect("/admin/edit_product/" + str(id))

    conn.close()

    return render_template(
        "add_color.html",
        product=product
    )
@app.route("/delete_color/<int:product_id>/<int:color_index>")
@app.route("/delete_color/<int:color_id>/<int:product_id>")
def delete_color(color_id, product_id):

    conn = get_connection()

    total_colors = conn.execute(
        """
        SELECT COUNT(*)
        FROM colors
        WHERE product_id = ?
        """,
        (product_id,)
    ).fetchone()[0]

    if total_colors > 1:

        conn.execute(
            """
            DELETE FROM colors
            WHERE id = ?
            """,
            (color_id,)
        )

        conn.commit()

        flash("🗑 Color deleted successfully!")

    else:

        flash("⚠ A product must have at least one color!")

    conn.close()

    return redirect("/admin/edit_product/" + str(product_id))
@app.route("/confirm_order/<string:order_id>")
def confirm_order(order_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_connection()

    conn.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE order_id = ?
        """,
        ("Confirmed", order_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_orders")
@app.route("/ship_order/<string:order_id>")
def ship_order(order_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_connection()

    conn.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE order_id = ?
        """,
        ("Shipped", order_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_orders")
@app.route("/payment_received/<string:order_id>")
def payment_received(order_id):
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_connection()

    conn.execute(
        """
        UPDATE orders
        SET status=?
        WHERE order_id = ?
        """,
        ("Paid", order_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_orders")
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin"] = True

            return redirect("/admin_orders")

        else:

            flash("Invalid Admin Credentials")

            return redirect("/admin/login")

    return render_template("admin_login.html")
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)