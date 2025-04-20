from flask import Flask, render_template, request
import os
from ingredient_utils import (
    extract_text,
    extract_ingredients,
    check_dietary_restrictions,
    check_toxic_ingredients
)

app = Flask(__name__)

# Folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global scan counter
scan_count = 0

# Dietary restriction mapping
RESTRICTION_MAP = {
    "vegan": [
        "milk", "cheese", "butter", "egg", "honey", "gelatin", "casein",
        "lactose", "whey", "albumin", "carmine", "shellac"
    ],
    "vegetarian": [
        "chicken", "beef", "pork", "fish", "shrimp", "anchovy", "gelatin",
        "lard", "meat", "broth"
    ],
    "pork_free": ["pork", "lard", "gelatin"],
    "beef_free": ["beef", "collagen", "tallow"],
    "nut_allergy": ["peanut", "almond", "cashew", "walnut", "hazelnut"],
    "gluten_free": ["wheat", "barley", "rye", "malt"],
    "fitness_friendly": ["sugar", "salt", "fat", "corn syrup", "maltodextrin"]
}

@app.route("/", methods=["GET", "POST"])
def index():
    global scan_count

    image_url = None
    ingredients_list = []
    results = {"restricted": "", "toxicity": {}}

    if request.method == "POST":
        image = request.files.get("image")
        if image:
            # Save uploaded image
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(image_path)
            image_url = f"/{image_path}"

            # Get selected dietary categories
            selected_categories = request.form.getlist("dietary")
            dietary_keywords = [
                item for category in selected_categories
                for item in RESTRICTION_MAP.get(category, [])
            ]

            # Extract ingredients and check for matches
            text = extract_text(image_path)
            ingredients_list = extract_ingredients(text)
            ingredients_combined = " ".join(ingredients_list)

            diet_flags = check_dietary_restrictions(ingredients_combined, selected_categories, RESTRICTION_MAP)
            tox_flags = check_toxic_ingredients(ingredients_combined)

            results["restricted"] = ", ".join(diet_flags) if diet_flags else "None 🎉"
            results["toxicity"] = {ingredient: "High" for ingredient in tox_flags}

            scan_count += 1

    return render_template(
        "index.html",
        image=image_url,
        ingredients=" ".join(ingredients_list),
        ingredients_extracted=ingredients_list,
        results=results,
        scan_count=scan_count
    )

# Sidebar pages
@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/stats")
def stats():
    return render_template("stats.html")

if __name__ == "__main__":
    app.run(debug=True)
