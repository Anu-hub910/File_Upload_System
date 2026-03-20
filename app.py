from flask import Flask, render_template, request, redirect, session, jsonify
import os, sqlite3, re, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- PATH SETUP ----------
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
DB_PATH = os.path.join(BASE_DIR, 'users.db')

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- FILE SETTINGS --------
ALLOWED_EXTENSIONS = {
    'png','jpg','jpeg','gif','webp',
    'pdf','txt','docx',
    'zip',
    'mp3','mp4'
}

IMAGE_EXTENSIONS = {'png','jpg','jpeg','gif','webp'}

# ---------- PASSWORD ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)')

    # Auto demo user
    conn.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        ("anusa58", hash_password("Har@123"))
    )

    conn.commit()
    conn.close()

# Initialize DB
init_db()

# ---------- UTIL ----------
def secure_filename(filename):
    return re.sub(r'[^\w.\-]', '_', filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    stat = os.stat(path)

    size = stat.st_size
    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')

    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024*1024:
        size_str = f"{size/1024:.1f} KB"
    else:
        size_str = f"{size/(1024*1024):.1f} MB"

    ext = filename.split('.')[-1].lower()

    return {
        "name": filename,
        "ext": ext,
        "is_image": ext in IMAGE_EXTENSIONS,
        "size": size_str,
        "modified": modified,
        "url": f"/static/uploads/{filename}"
    }

# ---------- AUTH ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = hash_password(request.form['password'])

        conn = sqlite3.connect(DB_PATH)
        data = conn.execute(
            'SELECT * FROM users WHERE username=? AND password=?',
            (user, pwd)
        ).fetchone()
        conn.close()

        if data:
            session['user'] = user
            return redirect('/')
        else:
            return "Invalid credentials"

    return render_template('login.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = hash_password(request.form['password'])

        conn = sqlite3.connect(DB_PATH)

        try:
            conn.execute('INSERT INTO users VALUES (?,?)', (user, pwd))
            conn.commit()
        except:
            conn.close()
            return "User already exists"

        conn.close()
        return redirect('/login')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ---------- MAIN ----------
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html', user=session['user'])

# ---------- FILE ----------
@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    files = request.files.getlist('file')
    uploaded = []

    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)

            path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(path):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.now().timestamp())}{ext}"

            file.save(os.path.join(UPLOAD_FOLDER, filename))
            uploaded.append(get_file_info(filename))

    return jsonify({"files": uploaded})


@app.route('/files')
def files():
    if 'user' not in session:
        return jsonify({"error":"Unauthorized"}), 401

    file_list = [
        get_file_info(f)
        for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]

    return jsonify({"files": file_list})


@app.route('/delete/<filename>', methods=['DELETE'])
def delete(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"message":"Deleted"})
    return jsonify({"error":"Not found"}), 404

# ---------- RUN ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)