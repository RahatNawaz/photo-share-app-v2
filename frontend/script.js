const API_URL = "http://127.0.0.1:5000";

const uploadForm = document.getElementById("uploadForm");

if (uploadForm) {
    uploadForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const formData = new FormData();

        formData.append("title", document.getElementById("title").value);
        formData.append("caption", document.getElementById("caption").value);
        formData.append("location", document.getElementById("location").value);
        formData.append("people", document.getElementById("people").value);
        formData.append("image", document.getElementById("image").files[0]);

        const message = document.getElementById("uploadMessage");
        message.innerText = "Uploading...";

        try {
            const response = await fetch(`${API_URL}/api/upload`, {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                message.innerText = "Image uploaded successfully!";
                uploadForm.reset();
            } else {
                message.innerText = result.error || "Upload failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

async function loadImages() {
    const gallery = document.getElementById("gallery");
    gallery.innerHTML = "<p>Loading images...</p>";

    try {
        const response = await fetch(`${API_URL}/api/images`);
        const images = await response.json();

        displayImages(images);
    } catch (error) {
        console.error(error);
        gallery.innerHTML = "<p>Could not load images.</p>";
    }
}

async function searchImages() {
    const keyword = document.getElementById("searchInput").value;
    const gallery = document.getElementById("gallery");

    gallery.innerHTML = "<p>Searching...</p>";

    try {
        const response = await fetch(`${API_URL}/api/search?q=${encodeURIComponent(keyword)}`);
        const images = await response.json();

        displayImages(images);
    } catch (error) {
        console.error(error);
        gallery.innerHTML = "<p>Search failed.</p>";
    }
}

function displayImages(images) {
    const gallery = document.getElementById("gallery");

    if (!images || images.length === 0) {
        gallery.innerHTML = "<p>No images found.</p>";
        return;
    }

    gallery.innerHTML = "";

    images.forEach(image => {
        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <img src="${image.imageUrl}" alt="${image.title}">
            <div class="card-content">
                <h3>${image.title || "Untitled"}</h3>
                <p>${image.caption || ""}</p>
                <p class="meta"><strong>Location:</strong> ${image.location || "N/A"}</p>
                <p class="meta"><strong>People:</strong> ${image.people || "N/A"}</p>
            </div>
        `;

        gallery.appendChild(card);
    });
}