from flask import Flask, render_template, request, Response, send_file, redirect, url_for, session, flash
import subprocess
import os
import json
import re
from datetime import datetime
from encrypt import decrypt_file, change_password, load_password
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clé secrète pour les sessions

TOOLS_FOLDER = "tools"
RAPPORT_FOLDER = "rapport"

# Fonctions helper pour les templates
def get_tool_name(filename):
    return filename.split('_')[0].capitalize()

def get_tool_icon(filename):
    icons = {
        'nmap': 'network-wired',
        'nikto': 'bug',
        'hydra': 'key',
        'sqlmap': 'database',
        'gobuster': 'folder',
        'feroxbuster': 'folder-open',
        'https_test': 'lock',
        'wireshark': 'chart-line'
    }
    tool = filename.split('_')[0]
    return icons.get(tool, 'file-alt')

def get_tool_color(filename):
    colors = {
        'nmap': 'primary',
        'nikto': 'danger',
        'hydra': 'warning',
        'sqlmap': 'info',
        'gobuster': 'success',
        'feroxbuster': 'link',
        'https_test': 'dark',
        'wireshark': 'light'
    }
    tool = filename.split('_')[0]
    return colors.get(tool, 'light')

def format_date(filename):
    match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})', filename)
    if match:
        date_str, time_str = match.groups()
        dt = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y à %H:%M")
    return "Date inconnue"

def get_tool_display_name(filename):
    names = {
        'nmap': 'Nmap',
        'nikto': 'Nikto',
        'hydra': 'Hydra',
        'sqlmap': 'SQLMap',
        'gobuster': 'Gobuster',
        'feroxbuster': 'Feroxbuster',
        'https_test': 'Test HTTPS',
        'wireshark': 'Wireshark'
    }
    tool = filename.split('_')[0]
    return names.get(tool, tool.capitalize())

def require_auth(f):
    """Décorateur pour vérifier l'authentification"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Ajouter les fonctions au contexte Jinja2
app.jinja_env.globals.update(
    get_tool_name=get_tool_name,
    get_tool_icon=get_tool_icon,
    get_tool_color=get_tool_color,
    get_tool_display_name=get_tool_display_name,
    format_date=format_date
)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        try:
            # Récupérer le mot de passe depuis MDP.json
            stored_password = load_password()
            if password == stored_password:
                session['authenticated'] = True
                flash("Connexion réussie !", "success")
                return redirect(url_for('index'))
            else:
                flash("Mot de passe incorrect.", "error")
        except Exception as e:
            flash(f"Erreur lors de la vérification : {e}", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('authenticated', None)
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('login'))

@app.route("/")
@require_auth
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
@require_auth
def scan():
    target = request.form.get("target")
    selected_tools = request.form.getlist("tools")

    def generate():
        for tool in selected_tools:
            yield f"→ Lancement de {tool}...\n"
            script_path = os.path.join(TOOLS_FOLDER, f"{tool}.py")

            if not os.path.isfile(script_path):
                yield f"[!] Script {tool}.py non trouvé.\n"
                continue

            try:
                process = subprocess.run(["python3", script_path, target], capture_output=True, text=True)
                if process.returncode == 0:
                    yield f"[✓] {tool} terminé.\n\n"
                else:
                    yield f"[✗] Erreur avec {tool} : {process.stderr}\n\n"
            except Exception as e:
                yield f"[!] Exception lors de l'exécution de {tool}: {e}\n"

    return Response(generate(), mimetype='text/plain')

@app.route("/rapports")
@require_auth
def list_rapports():
    fichiers = sorted(Path(RAPPORT_FOLDER).glob("*.html.aes"), reverse=True)
    return render_template("rapports.html", fichiers=[f.name for f in fichiers])

@app.route("/rapport/<nom>")
@require_auth
def lire_rapport(nom):
    chemin_chiffré = os.path.join(RAPPORT_FOLDER, secure_filename(nom))
    chemin_dechiffre = chemin_chiffré.replace(".aes", "")

    try:
        decrypt_file(chemin_chiffré, chemin_dechiffre)
        return send_file(chemin_dechiffre)
    except Exception as e:
        return f"Erreur lors du déchiffrement : {e}", 500
    finally:
        if os.path.exists(chemin_dechiffre):
            os.remove(chemin_dechiffre)

@app.route("/changepass", methods=["GET", "POST"])
@require_auth
def changer_mdp():
    if request.method == "POST":
        ancien = request.form.get("ancien")
        nouveau = request.form.get("nouveau")
        confirm = request.form.get("confirm")

        if nouveau != confirm:
            flash("Nouveau mot de passe et confirmation ne correspondent pas.", "error")
            return render_template("changepass.html")

        try:
            change_password(ancien, nouveau)
            flash("Mot de passe changé avec succès !", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Erreur : {e}", "error")

    return render_template("changepass.html")

if __name__ == "__main__":
    os.makedirs(RAPPORT_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
