from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Smart Technician</title>
        <style>
            body {
                font-family: Arial;
                background-color: #EAF2F8;
                text-align: center;
                padding-top: 80px;
            }

            h1 {
                color: #1F4E79;
                font-size: 40px;
            }

            p {
                font-size: 20px;
                color: #333333;
            }

            .version {
                color: #666666;
                font-weight: bold;
            }

            .academy {
                color: #555555;
                margin-top: 10px;
            }

            button {
                display: block;
                margin: 15px auto;
                width: 300px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                background-color: #1F4E79;
                color: white;
                cursor: pointer;
            }

            button:hover {
                background-color: #163A5C;
            }
        </style>
    </head>

    <body>

        <h1>AI SMART TECHNICIAN</h1>

        <div class="version">
            VERSION 1.0
        </div>

        <div class="academy">
            Pengajar: MESSI Skills Academy
        </div>

        <p>Sistem Bantuan Diagnosis Masalah Komputer</p>

        <button>DIAGNOSIS KOMPUTER</button>
        <button>DIAGNOSIS NETWORK</button>
        <button>UPLOAD GAMBAR</button>
        <button>TECHNICIAN REPORT</button>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
