import platform
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
import difflib
from typing import List, Dict

# === Set Tesseract Path for Windows ===
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# === Preprocess Image for OCR ===
def preprocess_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

# === OCR Text Extraction ===
def extract_text(image_path: str) -> str:
    processed_img = preprocess_image(image_path)
    return pytesseract.image_to_string(processed_img)

# === Ingredient Extraction Using Fuzzy Matching ===
def extract_ingredients(text: str) -> List[str]:
    text = text.lower().replace('\n', ' ')
    words = text.split()

    for i, word in enumerate(words):
        if difflib.SequenceMatcher(None, "ingredients", word).ratio() > 0.6:
            remaining_text = ' '.join(words[i + 1:])
            stop_words = [
                'contains', 'may contain', 'and/or', 'warnings', 'distributed by',
                'call', 'best when used by', 'keep refrigerated'
            ]
            for stop in stop_words:
                if stop in remaining_text:
                    remaining_text = remaining_text.split(stop)[0]
            cleaned = re.sub(r'[^\w\s,]', '', remaining_text)
            return [ing.strip() for ing in re.split(r',|\n', cleaned) if ing.strip()]
    return []

# === Dietary Restriction Matching ===
def check_dietary_restrictions(extracted_text: str, selected_categories: List[str], category_map: Dict[str, List[str]]) -> List[str]:
    text = extracted_text.lower()
    flagged = []
    for category in selected_categories:
        for item in category_map.get(category, []):
            if item.lower() in text:
                flagged.append(f"{item} ({category})")
    return flagged

# === Toxic Ingredient Matching ===
toxic_ingredients = ['sodium benzoate', 'aspartame', 'bht', 'bpa', 'msg', 'red 40']

def check_toxic_ingredients(text: str) -> List[str]:
    text = text.lower()
    return [toxic for toxic in toxic_ingredients if toxic in text]

# === Wrapper Function for Label Analysis ===
def analyze_label(image_path: str, selected_categories: List[str], category_map: Dict[str, List[str]]) -> Dict:
    text = extract_text(image_path)
    ingredients = extract_ingredients(text)
    diet_flags = check_dietary_restrictions(text, selected_categories, category_map)
    tox_flags = check_toxic_ingredients(text)

    return {
        "ingredients": ingredients,
        "diet_flags": diet_flags,
        "tox_flags": tox_flags
    }

# === Debugging / Test Mode ===
if __name__ == "__main__":
    category_map = {
        "vegan": ["milk", "cheese", "butter", "egg", "honey", "gelatin", "casein", "lactose", "whey", "albumin", "carmine", "shellac"],
        "vegetarian": ["chicken", "beef", "pork", "fish", "shrimp", "anchovy", "gelatin", "lard", "meat", "broth"],
        "pork_free": ["pork", "lard", "gelatin"],
        "beef_free": ["beef", "collagen", "tallow"],
        "nut_allergy": ["peanut", "almond", "cashew", "walnut", "hazelnut"],
        "gluten_free": ["wheat", "barley", "rye", "malt"],
        "fitness_friendly": ["sugar", "salt", "fat", "corn syrup", "maltodextrin"]
    }
    test_categories = ['vegan', 'nut_allergy', 'fitness_friendly']
    result = analyze_label("test3.png", test_categories, category_map)

    print("🧾 OCR Text:\n", extract_text("test3.png"))
    print("\n🍽️ Extracted Ingredients:", result['ingredients'])
    print("❌ Dietary Restrictions Found:", result['diet_flags'])
    print("☣️ Toxic Ingredients Found:", result['tox_flags'])
