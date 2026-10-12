e64
import io
import os
import re
import subprocess
from datetime import datetime

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ubah-kepada-kunci-rahsia-anda")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

STYLE = """
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#EAF2F8;color:#222}
header{background:#1F4E79;color:#fff;text-align:center;padding:22px 12px}
header h1{margin:0 0 8px;font-size:clamp(24px,4vw,34px)}
header p{margin:0}
main{max-width:900px;margin:24px auto;padding:0 14px 28px}
.card{background:#fff;padding:22px;border-radius:12px;box-shadow:0 2px 9px #00000012;margin-bottom:18px}
h2{color:#1F4E79;margin-top:0}
label{display:block;font-weight:bold;margin:14px 0 7px}
input[type=text],textarea,input[type=file]{width:100%;padding:11px;border:1px solid #b9c7d3;border-radius:7px;font-size:16px}
textarea{min-height:120px;resize:vertical}
.btn{display:inline-block;border:0;border-radius:7px;background:#1F4E79;color:white;padding:12px 16px;font-weight:bold;font-size:15px;text-decoration:none;cursor:pointer;margin:5px 5px 5px 0}
.blue{background:#2874A6}.green{background:#148F77}.purple{background:#7D3C98}.red{background:#C0392B}
.menu{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.menu .btn{text-align:center;margin:0;padding:18px 8px}
.result{white-space:pre-wrap;background:#f4f7fa;padding:14px;border-left:4px solid #2874A6;border-radius:5px;overflow-wrap:anywhere}
.muted{color:#555;font-size:14px}
img.preview{max-width:100%;max-height:340px;display:block;margin:12px 0;border-radius:8px}
footer{text-align:center;color:#555;padding:15px;font-size:13px}
"""

SHELL = """<!doctype html>
<html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} - AI Smart Technician</title><style>""" + STYLE + """</style></head>
<body><header><h1>AI SMART TECHNICIAN</h1><p>Sistem Bantuan Diagnosis Masalah Komputer</p></header>
<main>{{ body|safe }}</main><footer>MESSI SKILLS ACADEMY · Versi 1.0</footer></body></html>"""

def render_page(title, body):
    return render_template_string(SHELL, title=title, body=body)

def save_report(problem, diagnosis, advice):
    session["report_problem"] = problem
    session["report_diagnosis"] = diagnosis
    session["report_advice"] = advice

def get_report():
    return {
        "problem": session.get("report_problem", ""),
        "diagnosis": session.get("report_diagnosis", ""),
        "advice": session.get("report_advice", ""),
    }

@app.route("/")
def home():
    body = """
    <section class="card" style="text-align:center">
      <h2>Selamat Datang</h2>
      <p>Sistem bantuan untuk membantu teknisyen membuat pemeriksaan awal masalah komputer.</p>
      <a class="btn" href="{{ url_for('menu') }}">MULA SISTEM</a>
      <a class="btn red" href="{{ url_for('keluar') }}">KELUAR</a>
    </section>"""
    return render_page("Laman Utama", render_template_string(body))

@app.route("/menu")
def menu():
    body = """
    <section class="card">
      <h2>MENU UTAMA</h2>
      <p>SISTEM BANTUAN DIAGNOSIS MASALAH KOMPUTER</p>
      <div class="menu">
        <a class="btn" href="{{ url_for('diagnosis_komputer') }}">DIAGNOSIS KOMPUTER</a>
        <a class="btn blue" href="{{ url_for('diagnosis_network') }}">DIAGNOSIS NETWORK</a>
        <a class="btn green" href="{{ url_for('upload_gambar') }}">UPLOAD GAMBAR</a>
        <a class="btn purple" href="{{ url_for('technician_report') }}">TECHNICIAN REPORT (PDF)</a>
      </div>
      <p><a class="btn red" href="{{ url_for('home') }}">KELUAR MENU</a></p>
    </section>"""
    return render_page("Menu Utama", render_template_string(body))

@app.route("/diagnosis", methods=["GET", "POST"])
def diagnosis_komputer():
    result = ""
    masalah = ""
    if request.method == "POST":
        masalah = request.form.get("masalah", "").strip()
        p = masalah.lower()
        diagnosis = ""
        advice = ""
        if not masalah:
            result = "Sila masukkan masalah komputer."
        elif "tak hidup" in p or "tidak hidup" in p:
            diagnosis = "1. Kabel kuasa mungkin tidak disambungkan dengan baik.\\n2. Power supply (PSU) mungkin bermasalah.\\n3. Bekalan elektrik mungkin tidak stabil."
            advice = "Periksa kabel kuasa dan bekalan elektrik. Jika masih tidak hidup, minta teknisyen memeriksa PSU."
        elif any(w in p for w in ("slow", "lambat", "perlahan", "lembap")):
            diagnosis = "1. RAM mungkin tidak mencukupi.\\n2. Terlalu banyak program mungkin berjalan.\\n3. Ruang storan mungkin hampir penuh."
            advice = "Tutup program yang tidak diperlukan dan periksa penggunaan RAM serta ruang storan."
        elif "monitor" in p or "tiada paparan" in p:
            diagnosis = "1. Kabel HDMI/VGA/DisplayPort mungkin longgar.\\n2. Monitor mungkin tidak menerima isyarat.\\n3. RAM atau kad grafik mungkin bermasalah."
            advice = "Periksa kabel paparan dan pastikan monitor dihidupkan. Jika masih tiada paparan, dapatkan pemeriksaan teknisyen."
        elif any(w in p for w in ("internet", "wifi", "wi-fi", "rangkaian")):
            diagnosis = "1. Sambungan Wi-Fi mungkin bermasalah.\\n2. Kabel rangkaian mungkin bermasalah.\\n3. Router atau switch mungkin bermasalah."
            advice = "Periksa sambungan rangkaian, kabel LAN atau Wi-Fi, dan status router."
        elif any(w in p for w in ("panas", "overheat", "berhabuk", "habuk")):
            diagnosis = "1. Kipas komputer mungkin tidak berfungsi dengan baik.\\n2. Habuk mungkin terkumpul pada sistem penyejukan.\\n3. Aliran udara dalam casing mungkin terhalang."
            advice = "Matikan komputer sebelum pemeriksaan fizikal. Bersihkan habuk dengan kaedah selamat dan periksa kipas."
        elif "ram" in p:
            diagnosis = "1. RAM mungkin tidak dipasang dengan baik.\\n2. RAM atau slot mungkin kotor.\\n3. RAM mungkin mengalami kerosakan."
            advice = "Matikan komputer dan putuskan kuasa sebelum memeriksa RAM. Jika berterusan, uji dengan RAM yang diketahui baik."
        else:
            diagnosis = "Masalah belum dapat dikenal pasti daripada kata kunci yang dimasukkan."
            advice = "Terangkan simptom dengan lebih jelas dan lakukan pemeriksaan lanjutan. Ini panduan awal, bukan diagnosis muktamad."
        if diagnosis:
            save_report(masalah, diagnosis, advice)
            result = "KEMUNGKINAN PUNCA:\\n" + diagnosis + "\\n\\nCADANGAN TEKNISYEN:\\n" + advice
    body = """
    <section class="card"><h2>DIAGNOSIS KOMPUTER</h2>
    <form method="post"><label for="masalah">Masukkan masalah komputer yang dialami:</label>
    <input id="masalah" name="masalah" type="text" value="{{ masalah }}" placeholder="Contoh: komputer tidak hidup" required>
    <button class="btn" type="submit">ANALISIS MASALAH</button></form>
    {% if result %}<h3>Hasil Analisis</h3><div class="result">{{ result }}</div>{% endif %}
    <p><a class="btn red" href="{{ url_for('menu') }}">KEMBALI KE MENU</a></p></section>"""
    return render_page("Diagnosis Komputer", render_template_string(body, result=result, masalah=masalah))

@app.route("/network", methods=["GET", "POST"])
def diagnosis_network():
    result = ""
    alamat = ""
    if request.method == "POST":
        alamat = request.form.get("alamat", "").strip()
        if not alamat or len(alamat) > 253 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]*", alamat):
            result = "Sila masukkan alamat IP atau nama host yang sah."
        else:
            try:
                # Render biasanya menggunakan Linux, maka pilihan ping ialah -c dan -W.
                proc = subprocess.run(["ping", "-c", "4", "-W", "3", alamat],
                                      capture_output=True, text=True, timeout=16, check=False)
                output = proc.stdout or proc.stderr or "Tiada output daripada arahan ping."
                status = "STATUS: SAMBUNGAN BERJAYA" if proc.returncode == 0 else "STATUS: SAMBUNGAN GAGAL"
                result = status + "\\n\\n" + output[-4500:]
                save_report("Ujian ping ke " + alamat, result,
                            "Jika sambungan gagal, periksa internet, kabel LAN atau Wi-Fi, router dan alamat sasaran.")
            except subprocess.TimeoutExpired:
                result = "Ujian ping mengambil masa terlalu lama dan telah dihentikan."
            except Exception as exc:
                result = "Ujian ping gagal dijalankan: " + str(exc)
    body = """
    <section class="card"><h2>DIAGNOSIS NETWORK</h2>
    <form method="post"><label for="alamat">Masukkan alamat IP atau nama host:</label>
    <input id="alamat" name="alamat" type="text" value="{{ alamat }}" placeholder="Contoh: 8.8.8.8 atau google.com" required>
    <button class="btn blue" type="submit">UJIAN PING</button></form>
    {% if result %}<h3>Keputusan Ping</h3><div class="result">{{ result }}</div>{% endif %}
    <p class="muted">Sesetengah pelayan menyekat ping. Kegagalan ping tidak semestinya bermaksud laman web tidak boleh dibuka.</p>
    <a class="btn red" href="{{ url_for('menu') }}">KEMBALI KE MENU</a></section>"""
    return render_page("Diagnosis Network", render_template_string(body, result=result, alamat=alamat))

@app.route("/upload", methods=["GET", "POST"])
def upload_gambar():
    result = ""
    preview = ""
    if request.method == "POST":
        file = request.files.get("gambar")
        if not file or not file.filename:
            result = "Sila pilih gambar terlebih dahulu."
        else:
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                result = "Format gambar mesti JPG, JPEG atau PNG."
            else:
                try:
                    image = Image.open(file.stream)
                    image.verify()
                    file.stream.seek(0)
                    image = Image.open(file.stream)
                    image.thumbnail((700, 450))
                    if image.mode not in ("RGB", "L"):
                        image = image.convert("RGB")
                    fmt = "PNG" if ext == "png" else "JPEG"
                    out = io.BytesIO()
                    image.save(out, format=fmt)
                    preview = "data:image/" + ("png" if fmt == "PNG" else "jpeg") + ";base64," + base64.b64encode(out.getvalue()).decode("ascii")
                    name = filename.lower()
                    if any(w in name for w in ("berhabuk", "habuk", "overheat", "panas")):
                        problem = "Kemungkinan masalah penyejukan atau habuk pada komputer."
                        advice = "1. Bersihkan habuk pada kipas dan heatsink.\\n2. Pastikan kipas berfungsi dengan baik.\\n3. Pastikan aliran udara tidak terhalang."
                    elif any(w in name for w in ("monitor", "display", "paparan")):
                        problem = "Kemungkinan masalah paparan monitor atau sambungan kabel."
                        advice = "1. Periksa kabel HDMI/VGA/DisplayPort.\\n2. Pastikan monitor dihidupkan.\\n3. Periksa RAM dan kad grafik jika perlu."
                    elif "ram" in name:
                        problem = "Kemungkinan masalah pada RAM."
                        advice = "1. Periksa pemasangan RAM.\\n2. Putuskan kuasa sebelum memeriksa RAM.\\n3. Uji RAM atau slot lain jika perlu."
                    elif any(w in name for w in ("wifi", "lan", "network", "kabel")):
                        problem = "Kemungkinan masalah sambungan rangkaian."
                        advice = "1. Periksa kabel rangkaian.\\n2. Periksa port LAN.\\n3. Periksa sambungan Wi-Fi."
                    else:
                        problem = "Gambar dimuat naik, tetapi masalah belum dikenal pasti."
                        advice = "Periksa gambar dan keadaan komputer secara fizikal. Analisis ini berdasarkan nama fail, bukan pengecaman visual AI."
                    save_report("Analisis gambar: " + filename, problem, advice)
                    result = "Gambar berjaya dimuat naik.\\n\\nKEMUNGKINAN MASALAH:\\n" + problem + "\\n\\nCADANGAN TEKNISYEN:\\n" + advice
                except Exception:
                    result = "Fail tidak dapat dibaca sebagai gambar yang sah. Cuba fail JPG atau PNG."
    body = """
    <section class="card"><h2>UPLOAD GAMBAR</h2>
    <form method="post" enctype="multipart/form-data">
    <label for="gambar">Pilih gambar masalah komputer (JPG/PNG, maksimum 5 MB):</label>
    <input id="gambar" name="gambar" type="file" accept=".jpg,.jpeg,.png" required>
    <button class="btn green" type="submit">UPLOAD & ANALISIS GAMBAR</button></form>
    {% if preview %}<img class="preview" src="{{ preview }}" alt="Gambar yang dimuat naik">{% endif %}
    {% if result %}<h3>Hasil Analisis</h3><div class="result">{{ result }}</div>{% endif %}
    <p class="muted">Versi ini menggunakan nama fail sebagai petunjuk awal; ia belum menggunakan pengecaman visual AI sebenar.</p>
    <a class="btn red" href="{{ url_for('menu') }}">KEMBALI KE MENU</a></section>"""
    return render_page("Upload Gambar", render_template_string(body, result=result, preview=preview))

@app.route("/report", methods=["GET", "POST"])
def technician_report():
    info = get_report()
    if request.method == "POST":
        info = {
            "problem": request.form.get("problem", "").strip(),
            "diagnosis": request.form.get("diagnosis", "").strip(),
            "advice": request.form.get("advice", "").strip(),
        }
        if not all(info.values()):
            body = """<section class="card"><h2>TECHNICIAN REPORT</h2><p>Sila lengkapkan semua maklumat laporan.</p><a class="btn" href="{{ url_for('technician_report') }}">KEMBALI KE LAPORAN</a></section>"""
            return render_page("Technician Report", render_template_string(body))
        return make_pdf(info)
    body = """
    <section class="card"><h2>TECHNICIAN REPORT</h2>
    <p>Maklumat diagnosis terakhir akan diisi secara automatik. Semak dan ubah jika perlu.</p>
    <form method="post">
    <label for="problem">Masalah komputer:</label><input id="problem" name="problem" type="text" value="{{ info.problem }}" required>
    <label for="diagnosis">Diagnosis:</label><textarea id="diagnosis" name="diagnosis" required>{{ info.diagnosis }}</textarea>
    <label for="advice">Cadangan teknisyen:</label><textarea id="advice" name="advice" required>{{ info.advice }}</textarea>
    <button class="btn purple" type="submit">JANA PDF</button></form>
    <a class="btn red" href="{{ url_for('menu') }}">KEMBALI KE MENU</a></section>"""
    return render_page("Technician Report", render_template_string(body, info=info))

def make_pdf(info):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("AI Smart Technician - Technician Report")
    page_width, page_height = A4
    x, y = 50, page_height - 60
    max_width, line_height = page_width - 100, 16

    def write_text(text, font="Helvetica", size=11, after=0):
        nonlocal y
        pdf.setFont(font, size)
        for paragraph in str(text).splitlines() or [""]:
            lines = simpleSplit(paragraph, font, size, max_width) or [""]
            for line in lines:
                if y < 60:
                    pdf.showPage()
                    y = page_height - 60
                    pdf.setFont(font, size)
                safe_line = line.encode("latin-1", "replace").decode("latin-1")
                pdf.drawString(x, y, safe_line)
                y -= line_height
        y -= after

    write_text("AI SMART TECHNICIAN", "Helvetica-Bold", 20, 8)
    write_text("TECHNICIAN DIAGNOSTIC REPORT", "Helvetica-Bold", 14, 8)
    write_text("Tarikh / Masa: " + datetime.now().strftime("%d/%m/%Y %H:%M"), "Helvetica", 10, 16)
    write_text("MASALAH KOMPUTER", "Helvetica-Bold", 12, 2)
    write_text(info["problem"], "Helvetica", 11, 12)
    write_text("DIAGNOSIS", "Helvetica-Bold", 12, 2)
    write_text(info["diagnosis"], "Helvetica", 11, 12)
    write_text("CADANGAN TEKNISYEN", "Helvetica-Bold", 12, 2)
    write_text(info["advice"], "Helvetica", 11, 14)
    write_text("MESSI SKILLS ACADEMY", "Helvetica-Bold", 15)
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Technician_Report.pdf", mimetype="application/pdf")

@app.route("/keluar")
def keluar():
    return redirect(url_for("home"))

@app.errorhandler(413)
def too_large(_error):
    body = '<section class="card"><h2>Fail terlalu besar</h2><p>Sila pilih gambar yang tidak melebihi 5 MB.</p><a class="btn" href="/upload">Kembali</a></section>'
    return render_page("Fail Terlalu Besar", body), 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

