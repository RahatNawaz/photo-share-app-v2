from flask import Flask, request, jsonify
from flask_cors import CORS
from blob_service import upload_image
from dotenv import load_dotenv
load_dotenv()
import os
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
CORS(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

@app.route("/")
def home():
    return jsonify({"message": "Photo Share API is running"})

@app.route("/api/upload", methods=["POST"])
def upload():
    image = request.files.get("image")

    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    image_url = upload_image(image)

    title = request.form.get("title", "")
    caption = request.form.get("caption", "")
    location = request.form.get("location", "")
    people = request.form.get("people", "")

    auto_tags = []

    combined_text = f"{title} {caption} {location} {people}".lower()

    if "food" in combined_text or "restaurant" in combined_text:
        auto_tags.append("food")

    if "london" in combined_text or "bridge" in combined_text:
        auto_tags.append("travel")

    if "cricket" in combined_text or "football" in combined_text:
        auto_tags.append("sports")

    if "friend" in combined_text or "people" in combined_text:
        auto_tags.append("people")

    metadata = {
        "title": title,
        "caption": caption,
        "location": location,
        "people": people,
        "imageUrl": image_url,
        "tags": auto_tags
    }

    saved_data = save_metadata(metadata)

    return jsonify({
        "message": "Image uploaded successfully",
        "data": saved_data
    })

@app.route("/api/images", methods=["GET"])
def images():
    data = get_all_images()
    return jsonify(data)

@app.route("/api/search", methods=["GET"])
def search():
    keyword = request.args.get("q", "")
    data = search_images(keyword)
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

    item = container.read_item(item=image_id, partition_key=image_id)

    if "ratings" not in item:
        item["ratings"] = []

    item["ratings"].append(rating)

    container.replace_item(item=image_id, body=item)

    return jsonify({"message": "Rating added"})

@app.route("/api/images/<image_id>", methods=["GET"])
def get_single_image(image_id):
    item = container.read_item(item=image_id, partition_key=image_id)
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

    container.replace_item(item=image_id, body=item)

    return jsonify({
        "message": "Image metadata updated successfully",
        "data": item
    })

@app.route("/api/images/<image_id>/like", methods=["POST"])
def like_image(image_id):

    item = container.read_item(item=image_id, partition_key=image_id)

    if "likes" not in item:
        item["likes"] = 0

    item["likes"] += 1

    container.replace_item(item=image_id, body=item)

    return jsonify({
        "message": "Image liked",
        "likes": item["likes"]
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
    except:
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
    except:
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
    except:
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)