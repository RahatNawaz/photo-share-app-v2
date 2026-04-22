from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# Azure services (we will implement these next if not already done)
from blob_service import upload_image
from cosmos_service import save_metadata, get_all_images

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return jsonify({
        "message": "Photo Share API is running"
    })

# =========================
# UPLOAD IMAGE (CREATOR ONLY)
# =========================
@app.route("/upload", methods=["POST"])
def upload():
    try:
        # Get form data
        file = request.files["file"]
        title = request.form.get("title", "")
        caption = request.form.get("caption", "")
        location = request.form.get("location", "")
        people = request.form.get("people", "")

        # Upload to Azure Blob Storage
        image_url = upload_image(file)

        # Create metadata object
        image_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "caption": caption,
            "location": location,
            "people": people,
            "url": image_url
        }

        # Save metadata to Cosmos DB
        save_metadata(image_data)

        return jsonify({
            "status": "success",
            "data": image_data
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# GET ALL IMAGES (CONSUMER VIEW)
# =========================
@app.route("/images", methods=["GET"])
def images():
    try:
        data = get_all_images()
        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# GET SINGLE IMAGE (OPTIONAL)
# =========================
@app.route("/images/<image_id>", methods=["GET"])
def get_image(image_id):
    try:
        all_images = get_all_images()

        for img in all_images:
            if img.get("id") == image_id:
                return jsonify(img)

        return jsonify({"message": "Image not found"}), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# MAIN RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)