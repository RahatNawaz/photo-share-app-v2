from flask import Flask, request, jsonify
from flask_cors import CORS
from blob_service import upload_image
from cosmos_service import save_metadata, get_all_images, search_images

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({"message": "Photo Share API is running"})

@app.route("/api/upload", methods=["POST"])
def upload():
    image = request.files.get("image")

    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    image_url = upload_image(image)

    metadata = {
        "title": request.form.get("title"),
        "caption": request.form.get("caption"),
        "location": request.form.get("location"),
        "people": request.form.get("people"),
        "imageUrl": image_url
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)