from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from datetime import datetime, timezone
import pytz
import os
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter
from ingredient_utils import (
    extract_text,
    extract_ingredients,
    check_dietary_restrictions,
    check_toxic_ingredients
)

# === App Setup ===
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret in production

# === Configurations ===
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eatsafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === TimeZone ===
mountain_tz = pytz.timezone("US/Mountain")

# === Extensions ===
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# === Models ===
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hash in production!
    diet_preferences = db.Column(db.String(500))

class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_path = db.Column(db.String(300))
    ingredients = db.Column(db.Text)
    restricted = db.Column(db.Text)
    toxicity = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(mountain_tz))
    user = db.relationship("User", backref="scans")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === Dietary restriction mapping ===
RESTRICTION_MAP = {
    "vegan": ["milk", "cheese", "butter", "egg", "honey", "gelatin", "casein", "lactose", "whey", "albumin", "carmine", "shellac"],
    "vegetarian": ["chicken", "beef", "pork", "fish", "shrimp", "anchovy", "gelatin", "lard", "meat", "broth"],
    "pork_free": ["pork", "lard", "gelatin"],
    "beef_free": ["beef", "collagen", "tallow"],
    "nut_allergy": ["peanut", "almond", "cashew", "walnut", "hazelnut"],
    "gluten_free": ["wheat", "barley", "rye", "malt"],
    "fitness_friendly": ["sugar", "salt", "fat", "corn syrup", "maltodextrin"]
}

# === Routes ===

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    image_url = None
    ingredients_list = []
    results = {"restricted": "", "toxicity": {}}

    if request.method == "POST":
        image = request.files.get("image")
        if image:
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(image_path)
            image_url = f"/{image_path}"

            selected_categories = request.form.getlist("dietary")
            dietary_keywords = [item for category in selected_categories for item in RESTRICTION_MAP.get(category, [])]

            text = extract_text(image_path)
            ingredients_list = extract_ingredients(text)
            ingredients_combined = " ".join(ingredients_list)

            diet_flags = check_dietary_restrictions(ingredients_combined, selected_categories, RESTRICTION_MAP)
            tox_flags = check_toxic_ingredients(ingredients_combined)

            results["restricted"] = ", ".join(diet_flags) if diet_flags else "None 🎉"
            results["toxicity"] = {ingredient: "High" for ingredient in tox_flags}

            # Save to database
            new_scan = Scan(
                user_id=current_user.id,
                image_path=image_url,
                ingredients=", ".join(ingredients_list),
                restricted=results["restricted"],
                toxicity=", ".join(results["toxicity"].keys()),
                timestamp = datetime.now(mountain_tz)
            )
            db.session.add(new_scan)
            db.session.commit()

    # ✅ Scan count from database
    scan_count = Scan.query.filter_by(user_id=current_user.id).count()

    return render_template(
        "index.html",
        image=image_url,
        ingredients=" ".join(ingredients_list),
        ingredients_extracted=ingredients_list,
        results=results,
        scan_count=scan_count
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password", "danger")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        selected_prefs = request.form.getlist("dietary")
        prefs_str = ",".join(selected_prefs)

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "warning")
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw, diet_preferences=prefs_str)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created! Please login.", "success")
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "preferences":
            # Update dietary preferences
            updated_prefs = request.form.getlist("dietary")
            current_user.diet_preferences = ",".join(updated_prefs)
            db.session.commit()
            flash("Dietary preferences updated!", "success")

        elif form_type == "account":
            # Update username and/or password
            new_username = request.form.get("new_username")
            new_password = request.form.get("new_password")

            if new_username and new_username != current_user.username:
                # Check if new username already exists
                if User.query.filter_by(username=new_username).first():
                    flash("Username already taken. Please choose another.", "danger")
                    return redirect(url_for("profile"))
                current_user.username = new_username
                flash("Username updated!", "success")

            if new_password:
                current_user.password = generate_password_hash(new_password) # password hashing
                flash("Password updated!", "success")

            db.session.commit()

        return redirect(url_for("profile"))

    preferences = current_user.diet_preferences.split(",") if current_user.diet_preferences else []
    user_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.timestamp.desc()).all()

    return render_template("profile.html", preferences=preferences, scans=user_scans)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/history")
@login_required
def history():
    user_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.timestamp.desc()).all()
    return render_template("history.html", scans=user_scans)

@app.route("/stats")
@login_required
def stats():
    user_scans = Scan.query.filter_by(user_id=current_user.id).all()

    all_ingredients = []

    for scan in user_scans:
        if scan.ingredients:
            # Split the string and clean each ingredient
            ingredients = [i.strip().lower() for i in scan.ingredients.split(",") if i.strip()]
            all_ingredients.extend(ingredients)

    ingredient_data = Counter(all_ingredients).most_common()

    return render_template("stats.html", ingredient_data=ingredient_data)

# === App Runner ===
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
