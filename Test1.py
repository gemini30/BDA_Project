import pytesseract
import cv2
import numpy as np
from PIL import Image
# Add the full path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    img = cv2.imread(image_path)

    # Resize for better resolution
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=30)

    # Apply thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh

def extract_text(image_path):
    processed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_img)
    return text

import re

def extract_ingredients(text):
    # Common pattern: “Ingredients: sugar, salt, …”
    match = re.search(r'ingredients[:\-]*([\s\S]+)', text, re.IGNORECASE)
    if match:
        raw = match.group(1)

        # Stop processing if 'contains' or similar terms appear — keep only main list
        raw = re.split(r'\b(contains|may contain|and/or)\b', raw, flags=re.IGNORECASE)[0]

        # Remove unwanted characters
        raw = re.sub(r'[^\w\s,]', '', raw)  # removes symbols except commas and whitespace

        # Split into ingredients
        cleaned = re.split(r',|\n', raw)

        # Final clean-up
        ingredients = [ing.strip().lower() for ing in cleaned if ing.strip()]
        return ingredients
    return []


def check_dietary_restrictions(ingredients, restrictions):
    flagged = [ing for ing in ingredients if any(r in ing for r in restrictions)]
    return flagged

restrictions = ['milk', 'egg', 'gelatin', 'sugar']

# Basic sample toxic ingredient list (can be expanded)
toxic_ingredients = ['sodium benzoate', 'aspartame', 'bht', 'bpa', 'msg', 'red 40']

def check_toxic_ingredients(ingredients):
    flagged = [ing for ing in ingredients if ing in toxic_ingredients]
    return flagged

def analyze_label(image_path, dietary_restrictions):
    text = extract_text(image_path)
    print("OCR Text:\n", text)

    ingredients = extract_ingredients(text)
    print("\nExtracted Ingredients:", ingredients)

    diet_flags = check_dietary_restrictions(ingredients, dietary_restrictions)
    tox_flags = check_toxic_ingredients(ingredients)

    print("\n❌ Dietary Restricted Ingredients Found:", diet_flags)
    print("☣️ Toxic Ingredients Found:", tox_flags)

    return {
        "ingredients": ingredients,
        "diet_flags": diet_flags,
        "tox_flags": tox_flags
    }

# Sample usage
restrictions = ['milk', 'gelatin', 'egg','sugar']
result = analyze_label('test3.png', restrictions)

