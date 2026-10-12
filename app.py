
import os
import socket
import platform
import subprocess
from datetime import datetime
from flask import (
    Flask, request, redirect, url_for, session,
    flash, render_template_string, send_file
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai-technician-demo-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}

STYLE = """
<style>
body {
    font-family: Arial, sans-serif;
    background: #EAF2F8;
    text-align: center;
    margin: 0;
    color: #263238;
}
header {
    background: #1F4E79;
    color: white;
    padding: 25px;
}
main {
    max-width: 700px;
    margin: 25px auto;
    padding: 15px;
}
.card {
    background: white;
    padding: 25px;
    border-radius: 12px;
    margin-bottom: 20px;
}
h1, h2 { color: #1F4E79; }
header h1 { color: white; }
button, .btn {
    display: inline-block;
    background: #1F4E79;
    color: white;
    border: 0;
    border-radius: 7px;
    padding: 13px;
    margin: 8px;
    font-size: 16px;
    cursor: pointer;
    text-decoration: none;
}
button:hover, .btn:hover { background: #163A5C; }
input, textarea, select {
    box-sizing: border-box;
    width: 100%;
    padding: 12px;
    margin: 8px 0;
}
img { max-width: 100%; max-height: 350px; }
.notice { background: #edf5ff; padding: 12px; }
nav { padding: 10px; }
nav a { margin: 5px; }
</style>
"""

PAGE = """
<!DOCTYPE html>
<html lang="ms">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Smart Technician</title>
""" + STYLE + """
</head>
<body>
<header>
<h1>AI SMART TECHNICIAN</h1>
<p>VERSION 1.0</p>
<p>Pengajar: MESSI Skills Academy</p>
<p>Sistem Bantuan Diagnosis Masalah Komputer</p>
</header>

{% if session.get('logged_in') %}
<nav>
<a href="/">Menu Utama</a>
<a href="/logout">Keluar</a>
</nav>
{% endif %}

<main>
{% for message in get_flashed_messages() %}
<div class="notice">{{ message }}</div>
{% endfor %}
{{ content|safe }}
</main>
</body>
</html>
"""

def show(title, content, **values):
    return render_template_string(
        PAGE, title=title,
        content=render_template_string(content, **values)
    )

def login_check():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return None

@app.route("/")
def home():
    check = login_check()
    if check:
        return check

    content = """
    <div class="card">
    <h2>Menu Utama</h2>
    <p>Selamat datang ke sistem AI Smart Technician.</p>
    <a class="btn" href="/diagnosis">DIAGNOSIS KOMPUTER</a>
    <a class="btn" href="/network">DIAGNOSIS NETWORK</a>
    <a class="btn" href="/upload">UPLOAD GAMBAR</a>
    <a class="btn" href="/report">TECHNICIAN REPORT</a>
    </div>
    """
    return show("Menu Utama", content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("username", "").strip()
        if name:
            session["logged_in"] = True
            session["username"] = name
            return redirect(url_for("home"))

    content = """
    <div class="card">
    <h2>Masuk Sistem</h2>
    <form method="post">
    <input name="username" placeholder="Nama pengguna" required>
    <button type="submit">MASUK</button>
    </form>
    <p>Log masuk demo tanpa kata laluan.</p>
    </div>
    """
    return show("Log Masuk", content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/diagnosis", methods=["GET", "POST"])
def diagnosis():
    check = login_check()
    if check:
        return check

    result = ""
    if request.method == "POST":
        symptom = request.form.get("symptom", "").strip()
        s = symptom.lower()
        advice = []

        if any(x in s for x in ["lambat", "slow", "hang"]):
            advice += [
                "Semak penggunaan CPU dan RAM.",
                "Pastikan ruang storan mencukupi.",
                "Mulakan semula komputer dan semak aplikasi permulaan."
            ]
        if any(x in s for x in ["internet", "wifi", "network", "rangkaian"]):
            advice += [
                "Semak kabel atau sambungan Wi-Fi.",
                "Semak alamat IP dan gateway.",
                "Jalankan ujian ping."
            ]
        if any(x in s for x in ["tak hidup", "tidak hidup", "power"]):
            advice += [
                "Semak kabel kuasa dan soket.",
                "Pastikan suis kuasa dihidupkan."
            ]
        if any(x in s for x in ["skrin", "monitor", "paparan"]):
            advice += [
                "Semak kabel monitor.",
                "Pastikan monitor menggunakan input yang betul."
            ]
        if not advice:
            advice = [
                "Periksa kabel dan sambungan peranti.",
                "Catat mesej ralat yang dipaparkan.",
                "Jalankan pemeriksaan komponen secara berperingkat."
            ]

        session["symptom"] = symptom
        session["advice"] = advice
        result = "<h3>Cadangan Diagnosis</h3><p>" + symptom + "</p><ul>"
        result += "".join("<li>" + a + "</li>" for a in advice)
        result += "</ul><p>Cadangan ini perlu disahkan oleh teknisyen.</p>"

    content = """
    <div class="card">
    <h2>Diagnosis Komputer</h2>
    <form method="post">
    <textarea name="symptom" placeholder="Terangkan masalah komputer"
    required></textarea>
    <button type="submit">ANALISIS MASALAH</button>
    </form>
    {{ result|safe }}
    </div>
    """
    return show("Diagnosis", content, result=result)

@app.route("/network", methods=["GET", "POST"])
def network():
    check = login_check()
    if check:
        return check

    result = ""
    if request.method == "POST":
        host = request.form.get("host", "").strip()

        try:
            ip = socket.gethostbyname(host)
            option = "-n" if platform.system() == "Windows" else "-c"
            output = subprocess.run(
                ["ping", option, "1", host],
                capture_output=True, text=True,
                timeout=5, shell=False
            )
            status = "Ping berjaya" if output.returncode == 0 else "Ping gagal atau tiada respons"
            session["network_status"] = status
            session["network_host"] = host
            result = "<h3>" + status + "</h3><p>Alamat IP: " + ip + "</p>"
            result += "<pre>" + output.stdout[-1500:] + "</pre>"
        except Exception:
            result = "<p>Ujian gagal. Semak alamat hos atau cuba semula.</p>"

    content = """
    <div class="card">
    <h2>Diagnosis Network</h2>
    <form method="post">
    <input name="host" placeholder="Contoh: 8.8.8.8" required>
    <button type="submit">SEMAK SAMBUNGAN</button>
    </form>
    {{ result|safe }}
    <p>Nota: Render mungkin menyekat ujian ping.</p>
    </div>
    """
    return show("Diagnosis Network", content, result=result)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    check = login_check()
    if check:
        return check

    result = ""
    if request.method == "POST":
        file = request.files.get("image")
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED:
                name = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, name))
                session["image_name"] = name
                return redirect(url_for("view_image"))
            result = "Format gambar tidak dibenarkan."

    content = """
    <div class="card">
    <h2>Upload Gambar</h2>
    <form method="post" enctype="multipart/form-data">
    <input type="file" name="image" accept="image/*" required>
    <button type="submit">UPLOAD GAMBAR</button>
    </form>
    {{ result }}
    <p>Format: PNG, JPG, JPEG, GIF atau WEBP. Had 5 MB.</p>
    </div>
    """
    return show("Upload Gambar", content, result=result)

@app.route("/view-image")
def view_image():
    check = login_check()
    if check:
        return check

    name = session.get("image_name")
    if not name:
        return redirect(url_for("upload"))

    content = """
    <div class="card">
    <h2>Gambar Berjaya Dimuat Naik</h2>
    <img src="{{ url_for('image_file', name=name) }}">
    <p>Gambar dipaparkan untuk rujukan teknisyen.</p>
    <p>Analisis kerosakan daripada gambar belum automatik.</p>
    <a class="btn" href="/upload">Upload Gambar Lain</a>
    </div>
    """
    return show("Paparan Gambar", content, name=name)

@app.route("/image-file/<name>")
def image_file(name):
    check = login_check()
    if check:
        return check
    safe = secure_filename(name)
    return send_file(os.path.join(UPLOAD_FOLDER, safe))

@app.route("/report", methods=["GET", "POST"])
def report():
    check = login_check()
    if check:
        return check

    if request.method == "POST":
        notes = request.form.get("notes", "")
        lines = [
            "LAPORAN TEKNISYEN - AI SMART TECHNICIAN",
            "Tarikh: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Teknisyen: " + session.get("username", ""),
            "",
            "Simptom: " + session.get("symptom", "Belum dibuat"),
            "Cadangan: " + "; ".join(session.get("advice", [])),
            "",
            "Hos network: " + session.get("network_host", "Belum diuji"),
            "Status network: " + session.get("network_status", "Belum diuji"),
            "",
            "Catatan teknisyen: " + notes
        ]
        from io import BytesIO
        return send_file(
            BytesIO("\n".join(lines).encode("utf-8")),
            mimetype="text/plain",
            as_attachment=True,
            download_name="laporan_teknisyen.txt"
        )

    content = """
    <div class="card">
    <h2>Technician Report</h2>
    <p>Laporan akan mengandungi maklumat diagnosis yang dibuat dalam sesi ini.</p>
    <form method="post">
    <textarea name="notes" placeholder="Catatan teknisyen"></textarea>
    <button type="submit">JANA LAPORAN</button>
    </form>
    </div>
    """
    return show("Laporan", content)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
