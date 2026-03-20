const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const gallery = document.getElementById("gallery");
const fileCount = document.getElementById("fileCount");

const progressWrap = document.getElementById("progressWrap");
const progressFill = document.getElementById("progressFill");
const progressPercent = document.getElementById("progressPercent");
const progressFileName = document.getElementById("progressFileName");

// ===== TOAST =====
function showToast(msg, type="success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");

    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<div class="toast-dot"></div>${msg}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("hide");
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// ===== FILE ICONS =====
function getFileIcon(ext) {
    const icons = {
        pdf: "📄",
        docx: "📝",
        txt: "📄",
        zip: "🗜️",
        mp3: "🎵",
        mp4: "🎬"
    };
    return icons[ext] || "📁";
}

// ===== LOAD FILES =====
function loadFiles() {
    fetch('/files')
        .then(res => res.json())
        .then(data => {
            const files = data.files || [];
            gallery.innerHTML = '';
            fileCount.innerText = files.length + " files";

            if (files.length === 0) {
                gallery.innerHTML = document.getElementById("emptyState").outerHTML;
                return;
            }

            files.forEach(file => {
                const div = document.createElement("div");
                div.className = "file-card";

                let preview;

                if (file.is_image) {
                    preview = `<img src="${file.url}" class="card-preview">`;
                } else {
                    preview = `
                        <div class="card-icon-preview">
                            ${getFileIcon(file.ext)}
                            <div class="card-icon-ext">${file.ext}</div>
                        </div>
                    `;
                }

                div.innerHTML = `
                    ${preview}
                    <div class="card-body">
                        <div class="card-name">${file.name}</div>
                        <div class="card-meta">
                            <span>${file.size || ''}</span>
                            <div>
                                <a href="${file.url}" download title="Download">⬇</a>
                                <button onclick="deleteFile('${file.name}', this)" class="card-delete">✖</button>
                            </div>
                        </div>
                    </div>
                `;

                gallery.appendChild(div);
            });
        })
        .catch(() => showToast("Error loading files", "error"));
}

// ===== UPLOAD =====
function uploadFiles(files) {
    const formData = new FormData();

    // ✅ Loop for multiple files
    for (let i = 0; i < files.length; i++) {
        formData.append("file", files[i]);
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload");

    xhr.onload = function() {
        if (xhr.status === 200) {
            loadFiles();
        } else {
            alert("Upload failed");
        }
    };

    xhr.send(formData);
}

// ===== DELETE =====
function deleteFile(name, btn) {
    const card = btn.closest(".file-card");
    card.classList.add("removing");

    fetch(`/delete/${name}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(() => {
            setTimeout(() => {
                card.remove();
                showToast("Deleted successfully", "error");
                loadFiles();
            }, 300);
        })
        .catch(() => showToast("Delete failed", "error"));
}

// ===== DRAG & DROP =====
dropZone.addEventListener("dragover", e => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", e => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    uploadFiles(e.dataTransfer.files);
});

// ===== BROWSE =====
document.getElementById("browseLink").onclick = () => fileInput.click();

fileInput.addEventListener("change", () => {
    uploadFiles(fileInput.files);
});

// ===== INIT =====
loadFiles();