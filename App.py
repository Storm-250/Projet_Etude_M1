# app.py
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
import subprocess

app = Flask(__name__)
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

tools = {
    "Wireshark": "tools/wireshark.py",
    "Nikto": "tools/nikto.py",
    "Hydra": "tools/hydra.py",
    "Nmap": "tools/nmap_msf.py",
    "Feroxbuster": "tools/feroxbuster.py",
    "HTTPS Test": "tools/https_test.py",
    "OWASP ZAP": "tools/zap.py",
    "SQLmap": "tools/sqlmap.py",
    "Gobuster": "tools/gobuster.py"
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        selected_tools = request.form.getlist("tools")
        target = request.form["target"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for tool in selected_tools:
            script = tools[tool]
            subprocess.Popen(["python3", script, target, timestamp])

        return redirect(url_for("reports"))

    return render_template("index.html", tools=tools.keys())

@app.route("/reports")
def reports():
    files = os.listdir(REPORTS_DIR)
    files.sort(reverse=True)
    return render_template("reports.html", files=files)

@app.route("/reports/<filename>")
def report_file(filename):
    with open(os.path.join(REPORTS_DIR, filename), "r") as f:
        content = f.read()
    return f"<pre>{content}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
