from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "my-secret-key-123"

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
# Complaint table
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

# Home page
@app.route("/")
def home():
    return render_template("index.html")
# Complaint page
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if not session.get("user_id"):
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        location = request.form["location"]
        category = request.form["category"]

        new_complaint = Complaint(
            title=title,
            description=description,
            location=location,
            category=category,
            user_id=session["user_id"]
        )

        db.session.add(new_complaint)
        db.session.commit()

        return """
        <h2>Complaint submitted successfully!</h2>
        <a href="/my-complaints">
            <button>View My Complaints</button>
        </a>
        """

    user = User.query.get(session["user_id"])

    return render_template("complaint.html", user=user)
# Admin dashboard
# Admin login
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin")
        return "Invalid admin username or password!"

    return render_template("admin_login.html")
# Admin logout
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return "Admin logged out successfully!"
# Update complaint status
@app.route("/update-status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):

    if not session.get("admin_logged_in"):
        return "Please login as admin first!"

    complaint = Complaint.query.get(complaint_id)

    if complaint:
        complaint.status = request.form["status"]
        db.session.commit()

    return "Complaint status updated successfully!"
@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return "Please login as admin first!"

    complaints = Complaint.query.all()

    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status="Pending").count()
    in_progress = Complaint.query.filter_by(status="In Progress").count()
    resolved = Complaint.query.filter_by(status="Resolved").count()

    return render_template(
        "admin.html",
        complaints=complaints,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )
# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id

            return render_template("complaint.html", user=user)

        return "Invalid email or password!"

    return render_template("login.html")

# My complaints
@app.route("/my-complaints")
def my_complaints():

    if not session.get("user_id"):
        return "Please login first!"

    user_id = session["user_id"]

    user = User.query.get(user_id)

    complaints = Complaint.query.filter_by(user_id=user_id).all()

    return render_template(
        "my_complaints.html",
        complaints=complaints,
        user=user
    )



# Register
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered!"

        # Encrypt password
        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return "Registration successful!"

    return render_template("register.html")


# Create database
with app.app_context():
    db.create_all()
@app.route("/logout")
def logout():

    session.pop("user_id", None)

    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)