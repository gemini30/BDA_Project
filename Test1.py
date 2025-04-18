import platform
import pytesseract
import cv2
import numpy as np
from PIL import Image
import re

# Platform-specific Tesseract path
#if platform.system() == 'Windows':
#    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=30)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_text(image_path):
    processed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_img)
    return text

def extract_ingredients(text):
    match = re.search(r'ingredients[:\-]*([\s\S]+)', text, re.IGNORECASE)
    if match:
        raw = match.group(1)
        raw = re.split(r'\b(contains|may contain|and/or)\b', raw, flags=re.IGNORECASE)[0]
        raw = re.sub(r'[^\w\s,]', '', raw)
        cleaned = re.split(r',|\n', raw)
        ingredients = [ing.strip().lower() for ing in cleaned if ing.strip()]
        return ingredients
    return []

def check_dietary_restrictions(ingredients, restrictions):
    flagged = [ing for ing in ingredients if any(r in ing for r in restrictions)]
    return flagged

toxic_ingredients = ['sodium benzoate', 'aspartame', 'bht', 'bpa', 'msg', 'red 40']

def check_toxic_ingredients(ingredients):
    flagged = [ing for ing in ingredients if ing in toxic_ingredients]
    return flagged

def analyze_label(image_path, dietary_restrictions):
    text = extract_text(image_path)
    ingredients = extract_ingredients(text)
    diet_flags = check_dietary_restrictions(ingredients, dietary_restrictions)
    tox_flags = check_toxic_ingredients(ingredients)
    return {
        "ingredients": ingredients,
        "diet_flags": diet_flags,
        "tox_flags": tox_flags
    }

# Only run this when testing directly
if __name__ == "__main__":
    restrictions = ['milk', 'gelatin', 'egg', 'sugar']
    result = analyze_label('test3.png', restrictions)
    print("OCR Text:", extract_text('test3.png'))
    print("\nExtracted Ingredients:", result['ingredients'])
    print("❌ Dietary Restrictions Found:", result['diet_flags'])
    print("☣️ Toxic Ingredients Found:", result['tox_flags'])
