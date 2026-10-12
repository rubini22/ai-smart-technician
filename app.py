import os
from openai import OpenAI
import io
import re
import subprocess
from datetime import datetime

from flask import (
    Flask, request, render_template_string,
    send_file, session, redirect, url_for
)
from werkzeug.utils import secure_filename
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "ai-smart-technician-secret-key"
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

BG = "#EAF2F8"
BLUE = "#1F4E79"
RED = "#C0392B"
GREEN = "#148F77"
PURPLE = "#7D3C98"
LIGHT_BLUE = "#2874A6"

STYLE = """
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 25px 15px;
    background: #EAF2F8;
    font-family: Arial, sans-serif;
    color: #263746;
}
.container {
    max-width: 850px;
    margin: 20px auto;
    padding: 30px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 14px #00000015;
}
h1 {
    color: #1F4E79;
    text-align: center;
    font-size: 30px;
    margin-bottom: 8px;
}
h2 { color: #1F4E79; }
.subtitle { text-align: center; margin-bottom: 25px; }
.version { color: #C0392B; font-weight: bold; text-align: center; }
.academy { color: #1F4E79; font-weight: bold; text-align: center; }
.menu-title { color: #555; text-align: center; font-weight: bold; }
.description { text-align: center; margin: 20px 0; }
.button {
    display: block;
    width: 100%;
    padding: 14px;
    margin: 12px 0;
    border: none;
    border-radius: 7px;
    color: white;
    text-decoration: none;
    text-align: center;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}
.blue { background: #1F4E79; }
.lightblue { background: #2874A6; }
.green { background: #148F77; }
.purple { background: #7D3C98; }
.red { background: #C0392B; }
.grey { background: #626567; }
label { display: block; margin-top: 16px; font-weight: bold; }
input[type=text], input[type=file], textarea {
    width: 100%;
    padding: 12px;
    margin-top: 7px;
    border: 1px solid #ccd5dd;
    border-radius: 6px;
    font-family: Arial, sans-serif;
    font-size: 15px;
}
textarea { min-height: 110px; resize: vertical; }
.result {
    margin-top: 20px;
    padding: 16px;
    background: #F2F8FC;
    border-left: 5px solid #1F4E79;
    border-radius: 5px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}
img.preview { display: block; max-width: 100%; max-height: 350px;
    margin: 20px auto; border-radius: 8px; }
.footer { text-align: center; color: #667; font-size: 13px; margin-top: 25px; }
</style>
"""

def page(content, title="AI SMART TECHNICIAN"):
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ms">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{{ title }}</title>
      """ + STYLE + """
    </head>
    <body>
      {{ content|safe }}
      <div class="footer">AI SMART TECHNICIAN | MESSI SKILLS ACADEMY</div>
    </body>
    </html>
    """, content=content, title=title)

def save_report(problem, diagnosis, advice):
    session["report"] = {
        "problem": problem,
        "diagnosis": diagnosis,
        "advice": advice
    }


def diagnosis_computer(problem):
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )

        if not os.environ.get("OPENAI_API_KEY"):
            return (
                "API KEY TIDAK DIJUMPAI",
                "Sila semak OPENAI_API_KEY dalam Environment Variables di Render."
            )

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "Anda ialah AI Smart Technician, pembantu teknikal "
                "komputer dan rangkaian. Jawab dalam Bahasa Melayu. "
                "Analisis simptom yang diberikan. Berikan diagnosis "
                "yang berkemungkinan, punca masalah, langkah pemeriksaan "
                "dan cadangan penyelesaian yang selamat. Jangan mendakwa "
                "sesuatu komponen rosak tanpa bukti yang mencukupi. "
                "Jika maklumat tidak mencukupi, nyatakan perkara yang "
                "perlu diperiksa."
            ),
            input=problem
        )

        diagnosis = response.output_text.strip()

        advice = (
            "Ikuti langkah pemeriksaan yang dicadangkan oleh AI. "
            "Matikan komputer sebelum memeriksa komponen dalaman."
        )

        return diagnosis, advice

    except Exception as e:
        print("Ralat OpenAI:", str(e))
        return (
            "AI tidak dapat membuat diagnosis pada masa ini.",
            "Semak API key, baki kredit atau billing OpenAI, "
            "nama model dan log aplikasi di Render."
        )

def home():
    content = """
    <div class="container" style="max-width:750px; padding-top:65px; padding-bottom:55px;">
      <h1 style="font-size:34px;">AI SMART TECHNICIAN</h1>
      <p class="subtitle">Sistem Bantuan Diagnosis Masalah Komputer</p>
      <a class="button blue" href="/menu">MULA SISTEM</a>
      <a class="button red" href="/keluar">KELUAR</a>
    </div>
    """
    return page(content)

@app.route("/menu")

def menu():
    content = """
    <div class="container">
      <h1>AI SMART TECHNICIAN</h1>
      <p class="version">VERSION 1.0</p>
      <p class="academy">MESSI SKILLS ACADEMY</p>
      <p class="menu-title">MENU UTAMA</p>
      <p class="description">SISTEM BANTUAN DIAGNOSIS MASALAH KOMPUTER</p>

      <a class="button blue" href="/diagnosis">DIAGNOSIS KOMPUTER</a>
      <a class="button lightblue" href="/network">DIAGNOSIS NETWORK</a>
      <a class="button green" href="/upload">UPLOAD GAMBAR</a>
      <a class="button purple" href="/report">TECHNICIAN REPORT</a>
      <a class="button red" href="/keluar">KELUAR</a>
      <a class="button grey" href="/">KEMBALI KE HALAMAN UTAMA</a>
    </div>
    """
    return page(content)

@app.route("/diagnosis", methods=["GET", "POST"])
def diagnosis():
    result = ""
    if request.method == "POST":
        problem = request.form.get("problem", "").strip()
        if problem:
            diag, advice = diagnosis_computer(problem)
            save_report(problem, diag, advice)
            result = f"""
            <div class="result">
            <b>MASALAH:</b>
            {problem}

            <b>DIAGNOSIS:</b>
            {diag}

            <b>CADANGAN:</b>
            {advice}
            </div>
            """
        else:
            result = '<div class="result">Sila masukkan masalah komputer terlebih dahulu.</div>'

    content = """
    <div class="container">
      <h1>DIAGNOSIS KOMPUTER</h1>
      <form method="post">
        <label>Nyatakan masalah komputer:</label>
        <textarea name="problem" required placeholder="Contoh: Komputer lambat dan selalu panas"></textarea>
        <button class="button blue" type="submit">ANALISIS MASALAH</button>
      </form>
      """ + result + """
      <a class="button grey" href="/menu">KEMBALI KE MENU UTAMA</a>
    </div>
    """
    return page(content)

@app.route("/network", methods=["GET", "POST"])
def network():
    result = ""
    if request.method == "POST":
        host = request.form.get("host", "").strip()

        if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
            result = '<div class="result">Masukkan alamat IP atau nama hos yang sah.</div>'
        else:
            try:
                completed = subprocess.run(
                    ["ping", "-c", "4", "-W", "3", host],
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                output = completed.stdout or completed.stderr or "Tiada output diterima."
                diagnosis_text = (
                    "Ping menerima respons daripada hos."
                    if completed.returncode == 0
                    else "Ping gagal atau hos tidak memberikan respons."
                )
                save_report(
                    "Ujian ping ke " + host,
                    diagnosis_text,
                    "Semak alamat IP, kabel rangkaian, Wi-Fi, gateway dan firewall jika ping gagal."
                )
                result = '<div class="result"><b>KEPUTUSAN PING</b><br>' + \
                    "<br>".join(
                        line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        for line in output.splitlines()
                    ) + '</div>'
            except Exception as exc:
                result = '<div class="result">Ujian ping tidak dapat dijalankan: ' + \
                    str(exc).replace("<", "&lt;").replace(">", "&gt;") + '</div>'

    content = """
    <div class="container">
      <h1>DIAGNOSIS NETWORK</h1>
      <p>Masukkan alamat IP atau nama hos untuk menjalankan ujian ping.</p>
      <form method="post">
        <label>Alamat IP / Nama Hos:</label>
        <input type="text" name="host" required placeholder="Contoh: 8.8.8.8">
        <button class="button lightblue" type="submit">MULA UJIAN PING</button>
      </form>
      """ + result + """
      <a class="button grey" href="/menu">KEMBALI KE MENU UTAMA</a>
    </div>
    """
    return page(content)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    result = ""
    preview = ""

    if request.method == "POST":
        file = request.files.get("image")

        if not file or not file.filename:
            result = '<div class="result">Sila pilih gambar terlebih dahulu.</div>'
        else:
            filename = secure_filename(file.filename)
            extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            if extension not in ALLOWED_EXTENSIONS:
                result = '<div class="result">Format gambar yang dibenarkan ialah JPG, JPEG dan PNG.</div>'
            else:
                try:
                    image_bytes = file.read()
                    img = Image.open(io.BytesIO(image_bytes))
                    img.verify()

                    encoded = __import__("base64").b64encode(image_bytes).decode("ascii")
                    mime = "image/png" if extension == "png" else "image/jpeg"
                    preview = f'<img class="preview" src="data:{mime};base64,{encoded}" alt="Gambar yang dimuat naik">'

                    name = filename.lower()
                    if any(word in name for word in ["habuk", "dust", "panas", "overheat"]):
                        problem = "Gambar berkaitan habuk atau suhu komputer."
                        diag = "Kemungkinan pengumpulan habuk atau masalah pengudaraan."
                        advice = "Periksa kipas dan pengudaraan. Matikan komputer sebelum membersihkan habuk."
                    elif any(word in name for word in ["monitor", "display", "paparan", "screen"]):
                        problem = "Gambar berkaitan monitor atau paparan."
                        diag = "Kemungkinan masalah paparan atau sambungan monitor."
                        advice = "Periksa kabel paparan, sambungan monitor dan bekalan kuasa."
                    elif "ram" in name:
                        problem = "Gambar berkaitan RAM."
                        diag = "Kemungkinan masalah pemasangan atau memori RAM."
                        advice = "Minta juruteknik memeriksa RAM dengan komputer dimatikan."
                    elif any(word in name for word in ["wifi", "network", "lan", "kabel"]):
                        problem = "Gambar berkaitan rangkaian komputer."
                        diag = "Kemungkinan masalah sambungan rangkaian."
                        advice = "Periksa kabel LAN, Wi-Fi, router dan adapter rangkaian."
                    else:
                        problem = "Gambar komputer dimuat naik: " + filename
                        diag = "Gambar berjaya dimuat naik, tetapi masalah khusus tidak dapat disahkan melalui nama fail sahaja."
                        advice = "Periksa gambar dan masukkan simptom komputer dalam fungsi Diagnosis Komputer untuk analisis berdasarkan maklumat."

                    save_report(problem, diag, advice)
                    result = f"""
                    <div class="result">
                    <b>ANALISIS GAMBAR</b><br>
                    <b>Masalah:</b> {problem}<br>
                    <b>Diagnosis:</b> {diag}<br>
                    <b>Cadangan:</b> {advice}
                    </div>
                    """
                except Exception:
                    result = '<div class="result">Fail tersebut bukan gambar yang sah atau tidak dapat dibaca.</div>'

    content = """
    <div class="container">
      <h1>UPLOAD GAMBAR</h1>
      <p>Muat naik gambar komputer atau komponen yang ingin diperiksa.</p>
      <form method="post" enctype="multipart/form-data">
        <label>Pilih gambar (JPG, JPEG atau PNG):</label>
        <input type="file" name="image" accept=".jpg,.jpeg,.png" required>
        <button class="button green" type="submit">ANALISIS MASALAH</button>
      </form>
      """ + preview + result + """
      <a class="button grey" href="/menu">KEMBALI KE MENU UTAMA</a>
    </div>
    """
    return page(content)

def create_pdf(info):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 55
    y = height - 65

    pdf.setTitle("AI SMART TECHNICIAN - Technician Report")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColorRGB(31/255, 78/255, 121/255)
    pdf.drawCentredString(width / 2, y, "AI SMART TECHNICIAN")
    y -= 30

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, y, "TECHNICIAN DIAGNOSTIC REPORT")
    y -= 35

    pdf.setFont("Helvetica", 10)
    pdf.drawString(left, y, "Tarikh dan Masa: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    y -= 35

    sections = [
        ("MASALAH KOMPUTER", info.get("problem", "")),
        ("DIAGNOSIS", info.get("diagnosis", "")),
        ("CADANGAN TEKNISIEN", info.get("advice", ""))
    ]

    for heading, value in sections:
        if y < 100:
            pdf.showPage()
            y = height - 65

        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColorRGB(31/255, 78/255, 121/255)
        pdf.drawString(left, y, heading)
        y -= 22

        pdf.setFont("Helvetica", 11)
        pdf.setFillColorRGB(0, 0, 0)

        # Tukar aksara khas supaya serasi dengan fon PDF standard.
        safe_value = str(value).encode("latin-1", "replace").decode("latin-1")
        lines = simpleSplit(safe_value, "Helvetica", 11, width - 2 * left)

        for line in lines or ["-"]:
            if y < 65:
                pdf.showPage()
                y = height - 65
                pdf.setFont("Helvetica", 11)
            pdf.drawString(left, y, line)
            y -= 17

        y -= 18

    if y < 60:
        pdf.showPage()
        y = height - 65

    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColorRGB(31/255, 78/255, 121/255)
    pdf.drawCentredString(width / 2, y, "MESSI SKILLS ACADEMY")

    pdf.save()
    buffer.seek(0)
    return buffer

@app.route("/report", methods=["GET", "POST"])
def report():
    info = session.get("report", {})
    problem = request.form.get("problem", info.get("problem", ""))
    diagnosis_text = request.form.get("diagnosis", info.get("diagnosis", ""))
    advice = request.form.get("advice", info.get("advice", ""))

    if request.method == "POST":
        info = {
            "problem": problem.strip(),
            "diagnosis": diagnosis_text.strip(),
            "advice": advice.strip()
        }

        if not any(info.values()):
            message = '<div class="result">Sila isi maklumat laporan terlebih dahulu.</div>'
        else:
            pdf_file = create_pdf(info)
            return send_file(
                pdf_file,
                as_attachment=True,
                download_name="Technician_Report.pdf",
                mimetype="application/pdf"
            )
    else:
        message = ""

    content = """
    <div class="container">
      <h1>TECHNICIAN REPORT</h1>
      <p>Maklumat daripada diagnosis terakhir akan diisi secara automatik jika tersedia.</p>
      <form method="post">
        <label>Masalah Komputer:</label>
        <textarea name="problem">""" + problem.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + """</textarea>
        <label>Diagnosis:</label>
        <textarea name="diagnosis">""" + diagnosis_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + """</textarea>
        <label>Cadangan Teknisi:</label>
        <textarea name="advice">""" + advice.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + """</textarea>
        <button class="button purple" type="submit">JANA TECHNICIAN REPORT PDF</button>
      </form>
      """ + message + """
      <a class="button grey" href="/menu">KEMBALI KE MENU UTAMA</a>
    </div>
    """
    return page(content)

@app.route("/keluar")
def keluar():
    session.clear()
    return redirect(url_for("home"))

@app.errorhandler(413)
def file_too_large(error):
    return page("""
    <div class="container">
      <h1>FAIL TERLALU BESAR</h1>
      <p>Saiz maksimum gambar ialah 5 MB.</p>
      <a class="button grey" href="/upload">KEMBALI</a>
    </div>
    """), 413

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )






