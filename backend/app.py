from flask import Flask, request, jsonify
from flask_cors import CORS
from blob_service import upload_image
from dotenv import load_dotenv
load_dotenv()
import os
import re
from cosmos_service import (
    save_metadata,
    get_all_images,
    search_images,
    container
)
import random
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://photostorageacctt.z1.web.core.windows.net",
            "https://photosharefrontend.z1.web.core.windows.net",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    }
})

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

# =====================================================
# AUTO TAG GENERATION
# =====================================================
def clean_tag(tag):
    """Convert text into a clean tag format."""
    tag = str(tag).strip().lower()
    tag = re.sub(r"[^a-z0-9\s-]", "", tag)
    tag = re.sub(r"\s+", "-", tag)
    return tag.strip("-")


def generate_auto_tags(title="", caption="", location="", people=""):
    """Generate automatic tags from image title, caption, location and people fields."""
    combined_text = f"{title} {caption} {location} {people}".lower()
    tags = []

    keyword_map = {
        "food": ["food", "restaurant", "coffee", "cafe", "pizza", "burger", "meal", "dinner", "lunch", "breakfast", "dessert", "cake", "drink"],
        "travel": ["travel", "trip", "tour", "holiday", "vacation", "journey", "airport", "hotel", "landmark", "bridge", "museum", "city", "street"],
        "nature": ["nature", "tree", "flower", "forest", "mountain", "river", "lake", "sky", "sunset", "sunrise", "sea", "beach", "park", "garden"],
        "sports": ["sport", "sports", "cricket", "football", "soccer", "tennis", "basketball", "gym", "running", "match", "stadium"],
        "people": ["person", "people", "friend", "friends", "family", "group", "team", "portrait", "selfie", "crowd"],
        "architecture": ["building", "architecture", "tower", "church", "mosque", "temple", "palace", "house", "office", "skyscraper"],
        "technology": ["technology", "tech", "computer", "laptop", "phone", "software", "coding", "programming", "ai", "cloud", "azure"],
        "education": ["education", "university", "college", "school", "class", "study", "student", "library", "lecture"],
        "event": ["event", "party", "wedding", "birthday", "festival", "concert", "ceremony", "celebration"],
        "fashion": ["fashion", "clothes", "dress", "style", "outfit", "shirt", "shoes", "model"],
        "art": ["art", "painting", "drawing", "design", "gallery", "creative", "illustration"],
        "animal": ["animal", "cat", "dog", "bird", "horse", "wildlife", "pet"],
        "vehicle": ["car", "bus", "train", "bike", "bicycle", "motorbike", "vehicle", "boat", "ship"]
    }

    for tag, keywords in keyword_map.items():
        if any(keyword in combined_text for keyword in keywords):
            tags.append(tag)

    # Add useful location tag, for example london, paris, dhaka etc.
    if location:
        location_words = [clean_tag(word) for word in re.split(r"[,\s]+", location) if len(clean_tag(word)) >= 3]
        for word in location_words[:2]:
            if word and word not in tags:
                tags.append(word)

    # Add people tag if the creator filled the people field.
    if people and "people" not in tags:
        tags.append("people")

    # Fallback: if no category matched, use meaningful words from title/caption.
    if not tags:
        stop_words = {
            "the", "and", "with", "from", "this", "that", "photo", "image", "picture", "a", "an", "of", "in", "on", "at", "to", "my", "our"
        }
        words = re.findall(r"[a-zA-Z0-9]+", f"{title} {caption}".lower())
        for word in words:
            cleaned = clean_tag(word)
            if len(cleaned) >= 4 and cleaned not in stop_words and cleaned not in tags:
                tags.append(cleaned)
            if len(tags) >= 3:
                break

    # Final fallback so every uploaded image has at least one tag.
    if not tags:
        tags.append("photo")

    return tags[:6]


def add_missing_tags_to_image(item):
    """Ensure older images without tags still display generated tags in frontend."""
    if not item.get("tags"):
        item["tags"] = generate_auto_tags(
            item.get("title", ""),
            item.get("caption", ""),
            item.get("location", ""),
            item.get("people", "")
        )
    return item


@app.route("/")
def home():
    return jsonify({"message": "Photo Share API is running"})


@app.route("/api/upload", methods=["POST"])
def upload():
    image = request.files.get("image")
    creator_email = request.form.get("creatorEmail", "")
    creator_name = request.form.get("creatorName", "")

    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    image_url = upload_image(image)

    title = request.form.get("title", "")
    caption = request.form.get("caption", "")
    location = request.form.get("location", "")
    people = request.form.get("people", "")

    auto_tags = generate_auto_tags(title, caption, location, people)

    metadata = {
        "title": title,
        "caption": caption,
        "location": location,
        "people": people,
        "imageUrl": image_url,
        "tags": auto_tags,
        "creatorEmail": creator_email,
        "creatorName": creator_name,
        "likes": 0,
        "likedBy": [],
        "comments": [],
        "ratings": []
    }

    saved_data = save_metadata(metadata)

    return jsonify({
        "message": "Image uploaded successfully",
        "tags": auto_tags,
        "data": saved_data
    })


@app.route("/api/images", methods=["GET"])
def images():
    data = get_all_images()
    data = [add_missing_tags_to_image(item) for item in data]
    return jsonify(data)


@app.route("/api/search", methods=["GET"])
def search():
    keyword = request.args.get("q", "")
    data = search_images(keyword)
    data = [add_missing_tags_to_image(item) for item in data]
    return jsonify(data)


@app.route("/api/images/<image_id>/comment", methods=["POST"])
def add_comment(image_id):
    data = request.json
    comment = data.get("comment")

    item = container.read_item(item=image_id, partition_key=image_id)

    if "comments" not in item:
        item["comments"] = []

    item["comments"].append(comment)

    container.replace_item(item=image_id, body=item)

    return jsonify({"message": "Comment added"})


@app.route("/api/images/<image_id>/rating", methods=["POST"])
def add_rating(image_id):
    data = request.json
    rating = data.get("rating")
    consumer_email = data.get("consumerEmail")

    if not consumer_email:
        return jsonify({"error": "Consumer email is required"}), 400

    item = container.read_item(item=image_id, partition_key=image_id)

    if "ratings" not in item:
        item["ratings"] = []

    existing_rating = None

    for r in item["ratings"]:
        if r.get("email") == consumer_email:
            existing_rating = r
            break

    if existing_rating:
        existing_rating["rating"] = rating
        message = "Rating updated"
    else:
        item["ratings"].append({
            "email": consumer_email,
            "rating": rating
        })
        message = "Rating added"

    container.replace_item(item=image_id, body=item)

    return jsonify({
        "message": message,
        "ratings": item["ratings"]
    })


@app.route("/api/images/<image_id>", methods=["GET"])
def get_single_image(image_id):
    item = container.read_item(item=image_id, partition_key=image_id)
    item = add_missing_tags_to_image(item)
    return jsonify(item)


@app.route("/api/images/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    container.delete_item(item=image_id, partition_key=image_id)
    return jsonify({"message": "Image deleted successfully"})


@app.route("/api/images/<image_id>", methods=["PUT"])
def update_image(image_id):
    data = request.json

    item = container.read_item(item=image_id, partition_key=image_id)

    item["title"] = data.get("title", item.get("title"))
    item["caption"] = data.get("caption", item.get("caption"))
    item["location"] = data.get("location", item.get("location"))
    item["people"] = data.get("people", item.get("people"))
    item["tags"] = generate_auto_tags(
        item.get("title", ""),
        item.get("caption", ""),
        item.get("location", ""),
        item.get("people", "")
    )

    container.replace_item(item=image_id, body=item)

    return jsonify({
        "message": "Image metadata updated successfully",
        "data": item
    })


@app.route("/api/images/<image_id>/like", methods=["POST"])
def like_image(image_id):
    data = request.json
    consumer_email = data.get("consumerEmail")

    if not consumer_email:
        return jsonify({"error": "Consumer email is required"}), 400

    item = container.read_item(item=image_id, partition_key=image_id)

    if "likedBy" not in item:
        item["likedBy"] = []

    if consumer_email in item["likedBy"]:
        item["likedBy"].remove(consumer_email)
        message = "Image unliked"
    else:
        item["likedBy"].append(consumer_email)
        message = "Image liked"

    item["likes"] = len(item["likedBy"])

    container.replace_item(item=image_id, body=item)

    return jsonify({
        "message": message,
        "likes": item["likes"],
        "likedBy": item["likedBy"]
    })


@app.route("/api/consumer/register", methods=["POST"])
def consumer_register():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    user_id = f"consumer_{email}"

    existing_users = list(container.query_items(
        query="SELECT * FROM c WHERE c.type = 'consumer' AND c.email = @email",
        parameters=[{"name": "@email", "value": email}],
        enable_cross_partition_query=True
    ))

    if existing_users:
        return jsonify({"error": "Email already registered"}), 400

    verification_code = str(random.randint(100000, 999999))

    user = {
        "id": user_id,
        "type": "consumer",
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "verified": False,
        "verificationCode": verification_code
    }

    container.create_item(body=user)

    msg = Message(
        subject="Photo Share Verification Code",
        sender=app.config["MAIL_USERNAME"],
        recipients=[email]
    )

    msg.body = f"Your Photo Share verification code is: {verification_code}"

    mail.send(msg)

    return jsonify({
        "message": "Registration successful. Please check your email for verification code."
    })


@app.route("/api/consumer/verify", methods=["POST"])
def verify_consumer():
    data = request.json

    email = data.get("email")
    code = data.get("code")

    user_id = f"consumer_{email}"
    item = container.read_item(item=user_id, partition_key=user_id)

    if item.get("verificationCode") != code:
        return jsonify({"error": "Invalid verification code"}), 400

    item["verified"] = True
    item["verificationCode"] = None

    container.replace_item(item=user_id, body=item)

    return jsonify({"message": "Email verified successfully"})


@app.route("/api/consumer/login", methods=["POST"])
def consumer_login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    user_id = f"consumer_{email}"
    try:
        user = container.read_item(item=user_id, partition_key=user_id)
    except Exception:
        return jsonify({"error": "Invalid email or password"}), 400

    if user.get("type") != "consumer":
        return jsonify({"error": "Invalid email or password"}), 400

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 400

    if not user.get("verified"):
        return jsonify({"error": "Please verify your email before login"}), 403

    return jsonify({
        "message": "Login successful",
        "name": user["name"],
        "email": user["email"],
        "role": "consumer"
    })


@app.route("/api/creator/register", methods=["POST"])
def creator_register():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    user_id = f"creator_{email}"

    try:
        container.read_item(item=user_id, partition_key=user_id)
        return jsonify({"error": "Creator email already registered"}), 400
    except Exception:
        pass

    verification_code = str(random.randint(100000, 999999))

    user = {
        "id": user_id,
        "type": "creator",
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "verified": False,
        "verificationCode": verification_code
    }

    container.create_item(body=user)

    msg = Message(
        subject="Photo Share Creator Verification Code",
        sender=app.config["MAIL_USERNAME"],
        recipients=[email]
    )

    msg.body = f"Your creator verification code is: {verification_code}"

    mail.send(msg)

    return jsonify({
        "message": "Creator registered. Please check your email for verification code."
    })


@app.route("/api/creator/verify", methods=["POST"])
def verify_creator():
    data = request.json

    email = data.get("email")
    code = data.get("code")

    user_id = f"creator_{email}"

    item = container.read_item(item=user_id, partition_key=user_id)

    if item.get("verificationCode") != code:
        return jsonify({"error": "Invalid verification code"}), 400

    item["verified"] = True
    item["verificationCode"] = None

    container.replace_item(item=user_id, body=item)

    return jsonify({"message": "Creator email verified successfully"})


@app.route("/api/creator/login", methods=["POST"])
def creator_login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    user_id = f"creator_{email}"

    try:
        user = container.read_item(item=user_id, partition_key=user_id)
    except Exception:
        return jsonify({"error": "Invalid email or password"}), 400

    if user.get("type") != "creator":
        return jsonify({"error": "Invalid email or password"}), 400

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 400

    if not user.get("verified"):
        return jsonify({"error": "Please verify your creator email before login"}), 403

    return jsonify({
        "message": "Creator login successful",
        "name": user["name"],
        "email": user["email"],
        "role": "creator"
    })


@app.route("/api/creator/images", methods=["GET"])
def creator_images():
    creator_email = request.args.get("email", "")

    if not creator_email:
        return jsonify({"error": "Creator email is required"}), 400

    data = list(container.query_items(
        query="SELECT * FROM c WHERE c.creatorEmail = @creatorEmail",
        parameters=[
            {"name": "@creatorEmail", "value": creator_email}
        ],
        enable_cross_partition_query=True
    ))

    data = [add_missing_tags_to_image(item) for item in data]
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
