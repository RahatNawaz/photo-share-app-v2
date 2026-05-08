// =====================================================
// CONFIG
// =====================================================
// const API_URL = "http://127.0.0.1:5000";
const API_URL = "https://photo-share-api.azurewebsites.net";


// =====================================================
// CREATOR IMAGE UPLOAD
// =====================================================
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
        formData.append("creatorEmail", localStorage.getItem("creatorEmail"));
        formData.append("creatorName", localStorage.getItem("creatorName"));

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


// =====================================================
// CONSUMER GALLERY
// =====================================================
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

        const consumerEmail = localStorage.getItem("consumerEmail");

        const myRating = image.ratings
            ? image.ratings.find(r => r.email === consumerEmail)
            : null;

        const currentRating = myRating ? myRating.rating : "";

        card.innerHTML = `
            <div class="image-box">
                <img src="${image.imageUrl}" alt="${image.title}">
            </div>

            <div class="card-content">
                <h3>${image.title || "Untitled"}</h3>
                <p class="creator-text">From ${image.creatorEmail || "Unknown creator"}</p>

                <div class="post-actions">
                    <button class="like-btn" onclick="likeImage('${image.id}')">
                        ${
                            image.likedBy &&
                            image.likedBy.includes(localStorage.getItem("consumerEmail"))
                                ? "♥"
                                : "♡"
                        }
                    </button>
                    <span>${image.likes || 0} likes</span>
                    <span class="divider"></span>
                    <span class="rating-display">⭐ ${calculateAverage(image.ratings)}</span>
                </div>

                <div class="rating-box">
                    <select id="rating-${image.id}">
                        <option value="" ${currentRating === "" ? "selected" : ""}>Rate</option>
                        <option value="1" ${currentRating == 1 ? "selected" : ""}>★ 1</option>
                        <option value="2" ${currentRating == 2 ? "selected" : ""}>★ 2</option>
                        <option value="3" ${currentRating == 3 ? "selected" : ""}>★ 3</option>
                        <option value="4" ${currentRating == 4 ? "selected" : ""}>★ 4</option>
                        <option value="5" ${currentRating == 5 ? "selected" : ""}>★ 5</option>
                    </select>

                    <button onclick="addRating('${image.id}')">Rate</button>
                </div>

                <p class="meta"><strong>Location:</strong> ${image.location || "N/A"}</p>
                <p class="meta"><strong>People:</strong> ${image.people || "N/A"}</p>
                <p class="meta"><strong>Tags:</strong> ${(image.tags || []).join(", ") || "No tags"}</p>

                <hr>

                <div>
                    ${(image.comments || [])
                        .map(c => `<p><strong>${c.name || "Anonymous"}:</strong> ${c.text || c}</p>`)
                        .join("")}
                </div>

                <div class="comment-box">
                    <input type="text" id="comment-${image.id}" placeholder="Add a comment...">
                    <button onclick="addComment('${image.id}')">Post</button>
                </div>

                <a class="btn secondary details-btn" href="image.html?id=${image.id}">View Details</a>
            </div>
        `;

        gallery.appendChild(card);
    });
}


// =====================================================
// IMAGE DETAILS PAGE
// =====================================================
async function loadSingleImage() {
    const params = new URLSearchParams(window.location.search);
    const imageId = params.get("id");
    const container = document.getElementById("imageDetails");

    if (!imageId) {
        container.innerHTML = "<p>No image selected.</p>";
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/images/${imageId}`);
        const image = await response.json();

        const consumerEmail = localStorage.getItem("consumerEmail");

        const isLiked =
            image.likedBy &&
            image.likedBy.includes(consumerEmail);

        const myRating = image.ratings
            ? image.ratings.find(r => r.email === consumerEmail)
            : null;

        const currentRating = myRating ? myRating.rating : "";

        container.innerHTML = `
            <div class="card single-card">
                <div class="details-image-box">
                    <img src="${image.imageUrl}" alt="${image.title}">
                </div>

                <div class="card-content">
                    <h1>${image.title || "Untitled"}</h1>
                    <p>${image.caption || ""}</p>

                    <div class="post-actions">
                        <button class="like-btn" onclick="likeImage('${image.id}')">
                            ${isLiked ? "&#9829;" : "&#9825;"}
                        </button>

                        <span>${image.likes || 0} likes</span>
                        <span class="divider"></span>
                        <span class="rating-display">&#9733; ${calculateAverage(image.ratings)}</span>
                    </div>

                    <div class="rating-box">
                        <select id="rating-${image.id}">
                            <option value="" ${currentRating === "" ? "selected" : ""}>Rate</option>
                            <option value="1" ${currentRating == 1 ? "selected" : ""}>&#9733; 1</option>
                            <option value="2" ${currentRating == 2 ? "selected" : ""}>&#9733; 2</option>
                            <option value="3" ${currentRating == 3 ? "selected" : ""}>&#9733; 3</option>
                            <option value="4" ${currentRating == 4 ? "selected" : ""}>&#9733; 4</option>
                            <option value="5" ${currentRating == 5 ? "selected" : ""}>&#9733; 5</option>
                        </select>

                        <button onclick="addRating('${image.id}')">
                            ${currentRating ? "Update Rating" : "Rate"}
                        </button>
                    </div>

                    <p class="meta"><strong>Location:</strong> ${image.location || "N/A"}</p>
                    <p class="meta"><strong>People:</strong> ${image.people || "N/A"}</p>
                    <p class="meta"><strong>Tags:</strong> ${(image.tags || []).join(", ") || "No tags"}</p>

                    <hr>

                    <h3>Comments</h3>

                    <div>
                        ${(image.comments || [])
                            .map(c => `<p><strong>${c.name || "Anonymous"}:</strong> ${c.text || c}</p>`)
                            .join("")}
                    </div>

                    <div class="comment-box">
                        <input type="text" id="comment-${image.id}" placeholder="Add a comment...">
                        <button onclick="addComment('${image.id}')">Post</button>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error(error);
        container.innerHTML = "<p>Could not load image details.</p>";
    }
}


// =====================================================
// COMMENTS, RATINGS, LIKES
// =====================================================
async function addComment(imageId) {
    const input = document.getElementById(`comment-${imageId}`);
    const commentText = input.value;

    if (!commentText) return;

    const consumerName = localStorage.getItem("consumerName") || "Anonymous";

    const comment = {
        name: consumerName,
        text: commentText
    };

    await fetch(`${API_URL}/api/images/${imageId}/comment`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ comment })
    });

    refreshCurrentPage();
}

async function addRating(imageId) {
    const ratingValue = document.getElementById(`rating-${imageId}`).value;

    if (!ratingValue) {
        alert("Please select a rating");
        return;
    }

    await fetch(`${API_URL}/api/images/${imageId}/rating`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            rating: Number(ratingValue),
            consumerEmail: localStorage.getItem("consumerEmail")
        })
    });

    refreshCurrentPage();
}

async function likeImage(imageId) {
    await fetch(`${API_URL}/api/images/${imageId}/like`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            consumerEmail: localStorage.getItem("consumerEmail")
        })
    });

    refreshCurrentPage();
}

function calculateAverage(ratings) {
    if (!ratings || ratings.length === 0) {
        return "No ratings";
    }

    const values = ratings.map(r => {
        if (typeof r === "object") {
            if (typeof r.rating === "object") {
                return Number(r.rating.value);
            }

            return Number(r.rating || r.value);
        }

        return Number(r);
    });

    const sum = values.reduce((a, b) => a + b, 0);

    return (sum / values.length).toFixed(1);
}

function refreshCurrentPage() {
    if (window.location.pathname.includes("image.html")) {
        loadSingleImage();
    } else {
        loadImages();
    }
}


// =====================================================
// CREATOR DASHBOARD
// =====================================================
async function loadCreatorImages() {
    const gallery = document.getElementById("creatorGallery");
    gallery.innerHTML = "<p>Loading uploaded images...</p>";

    try {
        const creatorEmail = localStorage.getItem("creatorEmail");

        const response = await fetch(`${API_URL}/api/creator/images?email=${encodeURIComponent(creatorEmail)}`);
        
        const images = await response.json();

        if (!images || images.length === 0) {
            gallery.innerHTML = "<p>No uploads found.</p>";
            return;
        }

        gallery.innerHTML = "";

        images.forEach(image => {
            const card = document.createElement("div");
            card.className = "card";

            card.innerHTML = `
                <div class="image-box">
                    <img src="${image.imageUrl}" alt="${image.title}">
                </div>
                
                <div class="card-content">
                    <h3>${image.title || "Untitled"}</h3>
                    <p>${image.caption || ""}</p>

                    <p class="meta"><strong>Location:</strong> ${image.location || "N/A"}</p>
                    <p class="meta"><strong>People:</strong> ${image.people || "N/A"}</p>
                    <p class="meta"><strong>Tags:</strong> ${(image.tags || []).join(", ") || "No tags"}</p>

                    <p><strong>Comments:</strong> ${(image.comments || []).length}</p>
                    <div class="post-actions">
                        <span>♡ ${image.likes || 0} likes</span>
                        <span>⭐ ${calculateAverage(image.ratings)}</span>
                    </div>

                    <button onclick="editImage('${image.id}')">Edit</button>
                    <button onclick="deleteImage('${image.id}')">Delete</button>
                </div>
            `;

            gallery.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        gallery.innerHTML = "<p>Could not load creator dashboard.</p>";
    }
}

async function deleteImage(imageId) {
    const confirmDelete = confirm("Are you sure you want to delete this image?");

    if (!confirmDelete) return;

    try {
        const response = await fetch(`${API_URL}/api/images/${imageId}`, {
            method: "DELETE"
        });

        if (response.ok) {
            alert("Image deleted successfully.");
            loadCreatorImages();
        } else {
            alert("Failed to delete image.");
        }
    } catch (error) {
        console.error(error);
        alert("Could not connect to backend.");
    }
}

function editImage(imageId) {
    window.location.href = `edit-image.html?id=${imageId}`;
}


// =====================================================
// EDIT IMAGE METADATA
// =====================================================
async function loadEditForm() {
    const params = new URLSearchParams(window.location.search);
    const imageId = params.get("id");

    const response = await fetch(`${API_URL}/api/images/${imageId}`);
    const image = await response.json();

    document.getElementById("editTitle").value = image.title || "";
    document.getElementById("editCaption").value = image.caption || "";
    document.getElementById("editLocation").value = image.location || "";
    document.getElementById("editPeople").value = image.people || "";

    const form = document.getElementById("editImageForm");

    form.addEventListener("submit", async function(e) {
        e.preventDefault();

        const updatedData = {
            title: document.getElementById("editTitle").value,
            caption: document.getElementById("editCaption").value,
            location: document.getElementById("editLocation").value,
            people: document.getElementById("editPeople").value
        };

        const updateResponse = await fetch(`${API_URL}/api/images/${imageId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(updatedData)
        });

        if (updateResponse.ok) {
            document.getElementById("editMessage").innerText = "Metadata updated successfully!";
        } else {
            document.getElementById("editMessage").innerText = "Update failed.";
        }
    });
}


// =====================================================
// CONSUMER REGISTER / VERIFY / LOGIN / LOGOUT
// =====================================================
const consumerRegisterForm = document.getElementById("consumerRegisterForm");

if (consumerRegisterForm) {
    consumerRegisterForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const name = document.getElementById("registerName").value;
        const email = document.getElementById("registerEmail").value;
        const password = document.getElementById("registerPassword").value;

        const message = document.getElementById("registerMessage");
        message.innerText = "Registering and sending verification code...";

        try {
            const response = await fetch(`${API_URL}/api/consumer/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name, email, password })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem("pendingVerifyEmail", email);
                message.innerText = result.message;
                window.location.href = "verify-consumer.html";
            } else {
                message.innerText = result.error || "Registration failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

const verifyConsumerForm = document.getElementById("verifyConsumerForm");

if (verifyConsumerForm) {
    const savedEmail = localStorage.getItem("pendingVerifyEmail");

    if (savedEmail) {
        document.getElementById("verifyEmail").value = savedEmail;
    }

    verifyConsumerForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.getElementById("verifyEmail").value;
        const code = document.getElementById("verifyCode").value;

        const message = document.getElementById("verifyMessage");
        message.innerText = "Verifying...";

        try {
            const response = await fetch(`${API_URL}/api/consumer/verify`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, code })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.removeItem("pendingVerifyEmail");
                message.innerText = "Email verified successfully. You can now login.";
                setTimeout(() => {
                    window.location.href = "consumer-login.html";
                }, 1000);
            } else {
                message.innerText = result.error || "Verification failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

const consumerLoginForm = document.getElementById("consumerLoginForm");

if (consumerLoginForm) {
    consumerLoginForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.getElementById("consumerEmail").value;
        const password = document.getElementById("consumerPassword").value;

        const message = document.getElementById("consumerLoginMessage");
        message.innerText = "Logging in...";

        try {
            const response = await fetch(`${API_URL}/api/consumer/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem("role", result.role);
                localStorage.setItem("consumerName", result.name);
                localStorage.setItem("consumerEmail", result.email);

                window.location.href = "consumer.html";
            } else {
                message.innerText = result.error || "Login failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

function showLoggedInUser() {
    const userBox = document.getElementById("loggedInUser");

    if (userBox) {
        const name = localStorage.getItem("consumerName");
        userBox.innerText = name ? `Logged in as: ${name}` : "Logged in as: Consumer";
    }
}

function logoutConsumer() {
    localStorage.removeItem("role");
    localStorage.removeItem("consumerName");
    localStorage.removeItem("consumerEmail");

    window.location.href = "index.html";
}


// =====================================================
// CREATOR REGISTER / VERIFY / LOGIN
// =====================================================
const creatorRegisterForm = document.getElementById("creatorRegisterForm");

if (creatorRegisterForm) {
    creatorRegisterForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const name = document.getElementById("creatorRegisterName").value;
        const email = document.getElementById("creatorRegisterEmail").value;
        const password = document.getElementById("creatorRegisterPassword").value;

        const message = document.getElementById("creatorRegisterMessage");
        message.innerText = "Registering creator and sending verification code...";

        try {
            const response = await fetch(`${API_URL}/api/creator/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name, email, password })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem("pendingCreatorVerifyEmail", email);
                window.location.href = "verify-creator.html";
            } else {
                message.innerText = result.error || "Creator registration failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

const verifyCreatorForm = document.getElementById("verifyCreatorForm");

if (verifyCreatorForm) {
    const savedEmail = localStorage.getItem("pendingCreatorVerifyEmail");

    if (savedEmail) {
        document.getElementById("verifyCreatorEmail").value = savedEmail;
    }

    verifyCreatorForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.getElementById("verifyCreatorEmail").value;
        const code = document.getElementById("verifyCreatorCode").value;

        const message = document.getElementById("verifyCreatorMessage");
        message.innerText = "Verifying creator email...";

        try {
            const response = await fetch(`${API_URL}/api/creator/verify`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, code })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.removeItem("pendingCreatorVerifyEmail");
                message.innerText = "Creator verified successfully. You can now login.";

                setTimeout(() => {
                    window.location.href = "creator-login.html";
                }, 1000);
            } else {
                message.innerText = result.error || "Creator verification failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

const creatorLoginForm = document.getElementById("creatorLoginForm");

if (creatorLoginForm) {
    creatorLoginForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.getElementById("creatorEmail").value;
        const password = document.getElementById("creatorPassword").value;

        const message = document.getElementById("loginMessage");
        message.innerText = "Logging in...";

        try {
            const response = await fetch(`${API_URL}/api/creator/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem("role", result.role);
                localStorage.setItem("creatorName", result.name);
                localStorage.setItem("creatorEmail", result.email);

                window.location.href = "creator.html";
            } else {
                message.innerText = result.error || "Creator login failed.";
            }
        } catch (error) {
            console.error(error);
            message.innerText = "Could not connect to backend.";
        }
    });
}

function logoutCreator() {
    localStorage.removeItem("role");
    localStorage.removeItem("creatorName");
    localStorage.removeItem("creatorEmail");

    window.location.href = "index.html";
}