import os
from openai import OpenAI
import io
import re
import subprocess
import shutil
import socket
import base64
from markupsafe import escape
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

def page(content, title="AI SMART COMPUTER TECHNICIAN"):
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
      <div class="footer">AI SMART COMPUTER TECHNICIAN | MESSI SKILLS ACADEMY</div>
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
    problem_lower = problem.lower()

    # 1. Komputer lambat
    if any(k in problem_lower for k in [
        "lambat", "slow", "hang", "lag", "tersekat"
    ]):
        diagnosis = (
            "Kemungkinan punca: RAM tidak mencukupi, "
            "penggunaan CPU tinggi, storan hampir penuh "
            "atau terlalu banyak aplikasi berjalan."
        )
        advice = (
            "1. Tutup aplikasi yang tidak diperlukan.\n"
            "2. Semak penggunaan CPU dan RAM dalam Task Manager.\n"
            "3. Semak ruang kosong pada storan.\n"
            "4. Imbas komputer untuk malware jika perlu."
        )

    # 2. RAM berbunyi atau bunyi beep
    elif any(k in problem_lower for k in [
        "ram berbunyi", "bunyi beep", "bunyi bip",
        "beep", "bip", "ram"
    ]):
        diagnosis = (
            "Kemungkinan punca: RAM tidak dipasang dengan betul, "
            "sambungan RAM bermasalah atau terdapat masalah "
            "perkakasan lain. Bunyi beep sahaja tidak mengesahkan "
            "RAM rosak."
        )
        advice = (
            "1. Catat corak bunyi beep semasa komputer dihidupkan.\n"
            "2. Matikan komputer dan cabut bekalan kuasa.\n"
            "3. Minta juruteknik memeriksa dan memasang semula RAM "
            "dengan langkah keselamatan yang betul.\n"
            "4. Rujuk manual motherboard untuk maksud kod beep."
        )

    # 3. Komputer terlalu panas
    elif any(k in problem_lower for k in [
        "panas", "overheat", "overheating",
        "suhu tinggi", "kipas bising"
    ]):
        diagnosis = (
            "Kemungkinan punca: aliran udara terhalang, "
            "habuk terkumpul, kipas tidak berfungsi "
            "atau sistem penyejukan bermasalah."
        )
        advice = (
            "1. Pastikan lubang pengudaraan tidak terhalang.\n"
            "2. Periksa suhu dan kelajuan kipas.\n"
            "3. Matikan komputer sebelum pembersihan.\n"
            "4. Minta juruteknik memeriksa kipas dan sistem "
            "penyejukan jika masalah berterusan."
        )

    # 4. Komputer tidak boleh dihidupkan
    elif any(k in problem_lower for k in [
        "tidak boleh hidup", "tak boleh hidup",
        "tak hidup", "tidak hidup", "no power",
        "tak boleh on", "tidak boleh on"
    ]):
        diagnosis = (
            "Kemungkinan punca: bekalan kuasa terputus, "
            "kabel kuasa longgar, adapter rosak atau "
            "masalah pada power supply."
        )
        advice = (
            "1. Periksa sambungan kabel kuasa.\n"
            "2. Pastikan soket elektrik berfungsi.\n"
            "3. Periksa adapter jika menggunakan komputer riba.\n"
            "4. Jika masih gagal, minta juruteknik memeriksa "
            "bekalan kuasa dan perkakasan."
        )

    # 5. Skrin atau monitor bermasalah
    elif any(k in problem_lower for k in [
        "skrin", "screen", "monitor",
        "paparan", "display", "black screen"
    ]):
        diagnosis = (
            "Kemungkinan punca: kabel paparan longgar, "
            "monitor tidak menerima isyarat atau masalah "
            "pada adapter grafik."
        )
        advice = (
            "1. Pastikan monitor dihidupkan.\n"
            "2. Periksa kabel HDMI, DisplayPort atau VGA.\n"
            "3. Pilih input monitor yang betul.\n"
            "4. Jika skrin masih gelap, periksa komputer "
            "dan kad grafik."
        )

    # 6. Masalah Internet atau rangkaian
    elif any(k in problem_lower for k in [
        "internet", "wifi", "wi-fi", "network",
        "rangkaian", "tiada connection",
        "tiada sambungan", "tak boleh connect"
    ]):
        diagnosis = (
            "Kemungkinan punca: sambungan Wi-Fi atau kabel LAN "
            "bermasalah, konfigurasi IP tidak betul, "
            "gateway tidak dapat dicapai atau gangguan Internet."
        )
        advice = (
            "1. Periksa sambungan Wi-Fi atau kabel LAN.\n"
            "2. Jalankan ipconfig untuk menyemak konfigurasi IP.\n"
            "3. Uji sambungan menggunakan arahan ping.\n"
            "4. Semak router dan gateway jika sambungan gagal."
        )

    # 7. Komputer terlalu bising
    elif any(k in problem_lower for k in [
        "bising", "bunyi kuat", "bunyi pelik",
        "berbunyi kuat"
    ]):
        diagnosis = (
            "Kemungkinan punca: kipas longgar atau kotor, "
            "getaran komponen atau masalah pada storan mekanikal."
        )
        advice = (
            "1. Kenal pasti sumber bunyi.\n"
            "2. Periksa kipas dan pengudaraan.\n"
            "3. Sandarkan data jika bunyi datang daripada "
            "cakera keras mekanikal.\n"
            "4. Minta juruteknik memeriksa komponen jika bunyi "
            "berterusan."
        )

    # 8. Masalah lain
    else:
        diagnosis = (
            "Maklumat belum mencukupi untuk mengenal pasti "
            "punca masalah secara khusus."
        )
        advice = (
            "1. Nyatakan simptom dengan lebih terperinci.\n"
            "2. Catat mesej ralat yang dipaparkan.\n"
            "3. Nyatakan bila masalah mula berlaku.\n"
            "4. Periksa sambungan dan keadaan perkakasan "
            "yang berkaitan."
        )

    return diagnosis, advice

def home():

    content = """
    <div class="container" style="max-width:750px; padding-top:65px; padding-bottom:55px;">
      <h1 style="font-size:34px;">AI SMART COMPUTER TECHNICIAN</h1>
      <p class="subtitle">Sistem Bantuan Diagnosis Masalah Komputer</p>
      <a class="button blue" href="/menu">MULA SISTEM</a>
      <a class="button red" href="/keluar">KELUAR</a>
    </div>
    """
    return page(content)


@app.route("/")
def index():
    return home()


@app.route("/menu")

def menu():
    content = """
    <div class="container">
      <h1>AI SMART COMPUTER TECHNICIAN</h1>
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



def create_pdf(info):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 55
    y = height - 65

    pdf.setTitle("AI SMART COMPUTER TECHNICIAN - Technician Report")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColorRGB(31/255, 78/255, 121/255)
    pdf.drawCentredString(width / 2, y, "AI SMART COMPUTER TECHNICIAN")
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

 
@app.route("/network", methods=["GET", "POST"])
def network():
    result = ""

    if request.method == "POST":
        host = request.form.get("host", "").strip()

        if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
            result = (
                '<div class="result">'
                'Masukkan alamat IP atau nama hos yang sah.'
                '</div>'
            )
        else:
            try:
                with socket.create_connection(
                    (host, 443), timeout=5
                ):
                    status = "SAMBUNGAN BERJAYA"
                    detail = (
                        "Server berjaya menyambung ke "
                        + host
                        + " melalui port 443."
                    )

            except OSError:
                status = "SAMBUNGAN GAGAL"
                detail = (
                    "Server tidak dapat menyambung ke "
                    + host
                    + " melalui port 443. "
                    "Hos mungkin tidak tersedia atau port ditutup."
                )

            save_report(
                "Ujian sambungan ke " + host,
                status,
                detail
            )

            result = (
                '<div class="result"><b>'
                + status
                + '</b><br>'
                + detail
                + '</div>'
            )

    content = """
    <div class="container">
      <h1>DIAGNOSIS NETWORK</h1>
      <p>
        Uji sambungan dari server website ke alamat hos
        melalui port HTTPS 443.
      </p>
      <form method="post">
        <label>Alamat IP / Nama Hos:</label>
        <input type="text" name="host" required
               placeholder="Contoh: 1.1.1.1">
        <button class="button lightblue" type="submit">
          UJI SAMBUNGAN
        </button>
      </form>
      """ + result + """
      <a class="button grey" href="/menu">
        KEMBALI KE MENU UTAMA
      </a>
    </div>
    """

    return page(content)


@app.route("/report")
def report():
    info = session.get("report")

    if not info:
        content = """
        <div class="container">
            <h1>TECHNICIAN REPORT</h1>
            <div class="result">
                Belum ada laporan diagnosis.
                Sila buat diagnosis komputer atau rangkaian dahulu.
            </div>
            <a class="button blue" href="/diagnosis">
                DIAGNOSIS KOMPUTER
            </a>
            <a class="button lightblue" href="/network">
                DIAGNOSIS NETWORK
            </a>
            <a class="button grey" href="/menu">
                KEMBALI KE MENU UTAMA
            </a>
        </div>
        """
        return page(content)

    problem = escape(info.get("problem", ""))
    diagnosis_text = escape(info.get("diagnosis", ""))
    advice = escape(info.get("advice", ""))

    content = f"""
    <div class="container">
        <h1>TECHNICIAN REPORT</h1>

        <div class="result">
            <b>MASALAH</b>
            <p>{problem}</p>

            <b>DIAGNOSIS</b>
            <p>{diagnosis_text}</p>

            <b>CADANGAN TEKNISIEN</b>
            <p>{advice}</p>
        </div>

        <a class="button purple" href="/report/pdf">
            JANA / MUAT TURUN LAPORAN PDF
        </a>

        <a class="button grey" href="/menu">
            KEMBALI KE MENU UTAMA
        </a>
    </div>
    """
    return page(content)


@app.route("/report/pdf")
def report_pdf():
    info = session.get("report")

    if not info:
        return redirect(url_for("report"))

    pdf_file = create_pdf(info)

    return send_file(
        pdf_file,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="Technician_Report.pdf"
    )

@app.route("/keluar")
def keluar():
    session.clear()
    return redirect(url_for("index"))

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


