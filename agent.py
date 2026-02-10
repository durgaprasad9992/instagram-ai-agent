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
# LOAD ENVIRONMENT VARIABLES
# =========================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

IMAGE_FOLDER = "generated_images"
LOG_FILE = "instagram_post_log.csv"

# Create folders/log file
os.makedirs(IMAGE_FOLDER, exist_ok=True)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp", "image_url", "caption"])

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# =========================
# 1. Dynamic Prompt Generator
# =========================
landscapes = ["mountains", "river", "forest", "lake", "beach", "night street"]
times = ["sunrise", "sunset", "moonlight", "golden hour", "foggy morning"]
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
# 2. Generate AI Image
# =========================
def generate_image():
    prompt = generate_prompt()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    image_data = base64.b64decode(response.data[0].b64_json)
    image_path = f"{IMAGE_FOLDER}/img_{int(time.time())}.png"
    with open(image_path, "wb") as f:
        f.write(image_data)
    return image_path, prompt

# =========================
# 3. Generate Caption + Hashtags
# =========================
def generate_caption(prompt):
    text_prompt = f"""
Write a short, soothing Instagram caption for this scene: {prompt}.
Include 8 relevant hashtags about nature, peace, love, and travel.
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": text_prompt}],
        max_tokens=120
    )
    return response.choices[0].message.content.strip()

# =========================
# 4. Upload Image to Cloudinary
# =========================
def upload_image(path):
    res = cloudinary.uploader.upload(path)
    return res["secure_url"]

# =========================
# 5. Post to Instagram Graph API
# =========================
def post_instagram():
    for attempt in range(3):  # retry up to 3 times
        try:
            image_path, prompt = generate_image()
            caption = generate_caption(prompt)
            public_url = upload_image(image_path)

            # Create media container
            media_resp = requests.post(
                f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media",
                data={
                    "image_url": public_url,
                    "caption": caption,
                    "access_token": ACCESS_TOKEN
                }
            ).json()

            creation_id = media_resp.get("id")
            if not creation_id:
                raise Exception(f"Media container creation failed: {media_resp}")

            # Publish media
            publish_resp = requests.post(
                f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish",
                data={
                    "creation_id": creation_id,
                    "access_token": ACCESS_TOKEN
                }
            ).json()

            if "id" not in publish_resp:
                raise Exception(f"Media publish failed: {publish_resp}")

            print(f"[{datetime.now()}] Posted successfully: {public_url}")

            # Log the post
            with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([datetime.now(), public_url, caption])

            return

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(30)  # wait before retry

# =========================
# 6. Scheduler: Every 3 hours
# =========================
schedule.every(3).hours.do(post_instagram)

print("🚀 Instagram AI Agent Running...")

while True:
    schedule.run_pending()
    time.sleep(60)
