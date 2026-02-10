import os
import base64
import requests
import schedule
import time
import random
import csv
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# =========================
# LOAD ENV
# =========================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

IMAGE_FOLDER = "generated_images"
LOG_FILE = "post_log.csv"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp", "image_url", "caption"])

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# PROMPT ENGINE
# =========================
landscapes = ["mountains", "river", "forest", "lake", "beach", "night street"]
times = ["sunset", "sunrise", "moonlight", "golden hour", "foggy morning"]
activities = [
    "a boy and girl cycling",
    "a boy and girl walking together",
    "a couple riding a bicycle",
    "a couple strolling peacefully"
]
moods = ["dreamy", "cinematic", "soothing", "peaceful", "romantic"]

def generate_prompt():
    return f"{random.choice(landscapes)} at {random.choice(times)}, {random.choice(activities)}, {random.choice(moods)} atmosphere, ultra realistic, cinematic lighting"

# =========================
# IMAGE GENERATION
# =========================
def generate_image():
    prompt = generate_prompt()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )

    image_data = base64.b64decode(response.data[0].b64_json)
    path = f"{IMAGE_FOLDER}/img_{int(time.time())}.png"

    with open(path, "wb") as f:
        f.write(image_data)

    return path, prompt

# =========================
# CAPTION + HASHTAGS
# =========================
def generate_caption(prompt):
    text_prompt = f"""
    Write a calming Instagram caption for: {prompt}
    Add 8 relevant hashtag

