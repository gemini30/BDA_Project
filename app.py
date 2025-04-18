from flask import Flask, render_template, request
import os
from test import extract_text, extract_ingredients, check_dietary_restrictions, check_toxic_ingredients

app = Flask(__name__)

# Where uploaded images are stored
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Session-level scan count
scan_count = 0

@app.route("/", methods=["GET", "POST"])
def index():
    global scan_count

    image_url = None
    ingredients = []
    results = {"restricted": "", "toxicity": {}}

    if request.method == "POST":
        image = request.files["image"]
        if image:
            # Save image to upload folder
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(image_path)
            image_url = f"/{image_path}"

            # Get dietary restriction checkboxes
            selected_dietary = request.form.getlist("dietary")

            restriction_map = {
                "vegan": ["milk", "egg", "gelatin", "cheese", "honey"],
                "gluten_free": ["wheat", "barley", "rye", "malt"],
                "nut_allergy": ["peanut", "almond", "cashew", "walnut", "hazelnut"]
            }

            dietary_keywords = [item for group in selected_dietary for item in restriction_map.get(group, [])]

            # OCR + ingredient checks
            text = extract_text(image_path)
            ingredients = extract_ingredients(text)

            diet_flags = check_dietary_restrictions(ingredients, dietary_keywords)
            tox_flags = check_toxic_ingredients(ingredients)

            results["restricted"] = ", ".join(diet_flags) if diet_flags else "None 🎉"
            results["toxicity"] = {ing: "High" for ing in tox_flags}

            scan_count += 1

    return render_template(
        "index.html",
        image=image_url,
        ingredients=ingredients,
        results=results,
        scan_count=scan_count
    )

# Sidebar-linked routes in use
@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/stats")
def stats():
    return render_template("stats.html")

if __name__ == "__main__":
    app.run(debug=True)
