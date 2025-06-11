from flask import Flask, render_template, request, Response, send_file, redirect
import subprocess
import os
import json
from encrypt import decrypt_file, change_password
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

TOOLS_FOLDER = "tools"
RAPPORT_FOLDER = "rapport"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
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
def list_rapports():
    fichiers = sorted(Path(RAPPORT_FOLDER).glob("*.html.aes"), reverse=True)
    return render_template("rapports.html", fichiers=[f.name for f in fichiers])

@app.route("/rapport/<nom>")
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
def changer_mdp():
    if request.method == "POST":
        ancien = request.form.get("ancien")
        nouveau = request.form.get("nouveau")
        confirm = request.form.get("confirm")

        if nouveau != confirm:
            return "Nouveau mot de passe et confirmation ne correspondent pas."

        try:
            change_password(ancien, nouveau)
            return redirect("/")
        except Exception as e:
            return f"Erreur : {e}"

    return '''
    <h2>Changer le mot de passe AES</h2>
    <form method="post">
        Ancien mot de passe : <input type="password" name="ancien"><br><br>
        Nouveau mot de passe : <input type="password" name="nouveau"><br><br>
        Confirmer : <input type="password" name="confirm"><br><br>
        <button type="submit">Changer</button>
    </form>
    '''

if __name__ == "__main__":
    os.makedirs(RAPPORT_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
