from flask import Flask, render_template, request, Response, send_file, redirect, url_for, session, flash
import subprocess
import os
import json
import re
from datetime import datetime
from encrypt import decrypt_file, change_password, load_password
from pathlib import Path
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
app.secret_key = os.urandom(24)

TOOLS_FOLDER = "tools"
RAPPORT_FOLDER = "rapports"  # CHANGÉ: de "rapport" à "rapports"

# Liste des outils disponibles (sans wireshark)
AVAILABLE_TOOLS = {
    'nmap': {'name': 'Nmap', 'icon': 'network-wired', 'color': 'primary', 'script': 'nmap_msf.py'},
    'nikto': {'name': 'Nikto', 'icon': 'bug', 'color': 'danger', 'script': 'nikto.py'},
    'hydra': {'name': 'Hydra', 'icon': 'key', 'color': 'warning', 'script': 'hydra.py'},
    'sqlmap': {'name': 'SQLMap', 'icon': 'database', 'color': 'info', 'script': 'sqlmap.py'},
    'gobuster': {'name': 'Gobuster', 'icon': 'folder', 'color': 'success', 'script': 'gobuster.py'},
    'feroxbuster': {'name': 'Feroxbuster', 'icon': 'folder-open', 'color': 'link', 'script': 'feroxbuster.py'},
    'https_test': {'name': 'Test HTTPS', 'icon': 'lock', 'color': 'dark', 'script': 'https_test.py'}
}

# Fonctions helper pour les templates
def get_tool_name(filename):
    """Extraire le nom de l'outil depuis le nom de fichier"""
    try:
        tool_key = filename.split('_')[0]
        return AVAILABLE_TOOLS.get(tool_key, {}).get('name', tool_key.capitalize())
    except:
        return "Inconnu"

def get_tool_icon(filename):
    """Extraire l'icône de l'outil depuis le nom de fichier"""
    try:
        tool_key = filename.split('_')[0]
        return AVAILABLE_TOOLS.get(tool_key, {}).get('icon', 'file-alt')
    except:
        return 'file-alt'

def get_tool_color(filename):
    """Extraire la couleur de l'outil depuis le nom de fichier"""
    try:
        tool_key = filename.split('_')[0]
        return AVAILABLE_TOOLS.get(tool_key, {}).get('color', 'light')
    except:
        return 'light'

def format_date(filename):
    """Formater la date depuis le nom de fichier"""
    try:
        # Pattern: tool_YYYY-MM-DD_HH-MM-SS.html.aes
        match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})', filename)
        if match:
            date_str, time_str = match.groups()
            dt = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y à %H:%M")
    except Exception as e:
        print(f"Erreur formatage date pour {filename}: {e}")
    return "Date inconnue"

def get_tool_display_name(filename):
    """Alias pour get_tool_name pour compatibilité"""
    return get_tool_name(filename)

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
    format_date=format_date,
    available_tools=AVAILABLE_TOOLS
)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        try:
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
    
    print(f"DEBUG: Target reçu = '{target}'")
    print(f"DEBUG: Outils sélectionnés = {selected_tools}")
    
    if not target:
        return Response("❌ Aucune cible spécifiée.\n", mimetype='text/plain')
    
    if not selected_tools:
        return Response("❌ Aucun outil sélectionné.\n", mimetype='text/plain')

    def generate():
        import sys
        import time
        
        total_tools = len(selected_tools)
        
        messages = [
            f"🎯 Début du scan de {target}\n",
            f"📋 {total_tools} outil(s) sélectionné(s): {', '.join(selected_tools)}\n",
            f"📁 Rapports sauvegardés dans: {RAPPORT_FOLDER}/\n",
            f"{'='*50}\n\n"
        ]
        
        for msg in messages:
            yield f"data: {msg}\n\n"
            sys.stdout.flush()
            
        time.sleep(0.1)
        
        for i, tool in enumerate(selected_tools, 1):
            if tool not in AVAILABLE_TOOLS:
                yield f"data: [{i}/{total_tools}] ❌ Outil '{tool}' non reconnu.\n\n\n\n"
                continue
                
            tool_info = AVAILABLE_TOOLS[tool]
            script_name = tool_info['script']
            script_path = os.path.join(TOOLS_FOLDER, script_name)
            
            yield f"data: [{i}/{total_tools}] 🚀 Lancement de {tool_info['name']}...\n\n\n\n"
            sys.stdout.flush()
            
            if not os.path.isfile(script_path):
                yield f"data: [{i}/{total_tools}] ❌ Script {script_name} non trouvé dans {TOOLS_FOLDER}/\n\n\n\n"
                continue

            try:
                yield f"data: [{i}/{total_tools}] ⚙️ Exécution en cours...\n\n\n\n"
                sys.stdout.flush()
                
                process = subprocess.run(
                    ["python3", script_path, target], 
                    capture_output=True, 
                    text=True,
                    timeout=600  # Augmenté à 10 minutes
                )
                
                if process.returncode == 0:
                    yield f"data: [{i}/{total_tools}] ✅ {tool_info['name']} terminé avec succès.\n\n\n\n"
                    if process.stdout.strip():
                        yield f"data: [{i}/{total_tools}] 📄 Sortie: {process.stdout.strip()[:200]}...\n\n\n\n"
                else:
                    yield f"data: [{i}/{total_tools}] ⚠️ {tool_info['name']} terminé avec des erreurs.\n\n\n\n"
                    if process.stderr.strip():
                        yield f"data: [{i}/{total_tools}] 🔍 Erreur: {process.stderr.strip()[:200]}...\n\n\n\n"
                        
            except subprocess.TimeoutExpired:
                yield f"data: [{i}/{total_tools}] ⏰ Timeout: {tool_info['name']} a dépassé la limite de temps (10 min).\n\n\n\n"
            except Exception as e:
                yield f"data: [{i}/{total_tools}] 💥 Exception lors de l'exécution de {tool_info['name']}: {str(e)}\n\n\n\n"
            
            yield f"data: [{i}/{total_tools}] {'─'*30}\n\n\n\n"
            sys.stdout.flush()
            time.sleep(0.1)
        
        yield f"data: 🏁 Scan terminé ! Consultez la section 'Rapports' pour voir les résultats.\n\n\n\n"
        yield f"data: 📁 Rapports disponibles dans le dossier: {RAPPORT_FOLDER}/\n\n\n\n"
        yield f"data: {'='*50}\n\n\n\n"

    response = Response(generate(), mimetype='text/plain')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route("/rapports")
@require_auth
def list_rapports():
    """Liste tous les rapports chiffrés disponibles"""
    fichiers = []
    
    # Créer le dossier s'il n'existe pas
    os.makedirs(RAPPORT_FOLDER, exist_ok=True)
    
    try:
        # Chercher tous les fichiers .html.aes dans le dossier rapports
        rapport_path = Path(RAPPORT_FOLDER)
        
        # Debug: afficher le contenu du dossier
        all_files = list(rapport_path.glob("*"))
        print(f"DEBUG: Tous les fichiers dans {RAPPORT_FOLDER}: {[f.name for f in all_files]}")
        
        # Chercher les fichiers .html.aes (et .aes au cas où)
        aes_files = list(rapport_path.glob("*.html.aes")) + list(rapport_path.glob("*.aes"))
        print(f"DEBUG: Fichiers .aes trouvés: {[f.name for f in aes_files]}")
        
        for f in sorted(aes_files, key=lambda x: x.stat().st_mtime, reverse=True):
            # Exclure wireshark et autres outils non autorisés
            if not f.name.startswith('wireshark_'):
                fichiers.append(f.name)
                print(f"DEBUG: Fichier ajouté à la liste: {f.name}")
            else:
                print(f"DEBUG: Fichier exclu (wireshark): {f.name}")
                
        print(f"DEBUG: Fichiers à afficher dans l'interface: {fichiers}")
        
    except Exception as e:
        print(f"Erreur lors de la lecture du dossier rapports: {e}")
        flash(f"Erreur lors de la lecture des rapports: {e}", "error")
    
    return render_template("rapports.html", fichiers=fichiers)

@app.route("/rapport/<nom>")
@require_auth
def lire_rapport(nom):
    """Lire un rapport spécifique"""
    # Sécurité : vérifier que le nom ne commence pas par wireshark
    if nom.startswith('wireshark_'):
        flash("Accès non autorisé à ce rapport.", "error")
        return redirect(url_for('list_rapports'))
        
    chemin_chiffré = os.path.join(RAPPORT_FOLDER, secure_filename(nom))
    
    # Déterminer le chemin déchiffré
    if nom.endswith('.html.aes'):
        chemin_dechiffre = chemin_chiffré.replace(".html.aes", ".html")
    elif nom.endswith('.aes'):
        chemin_dechiffre = chemin_chiffré.replace(".aes", "")
    else:
        flash("Format de fichier non supporté.", "error")
        return redirect(url_for('list_rapports'))

    try:
        if not os.path.exists(chemin_chiffré):
            flash(f"Fichier {nom} introuvable.", "error")
            return redirect(url_for('list_rapports'))
            
        decrypt_file(chemin_chiffré, chemin_dechiffre)
        return send_file(chemin_dechiffre)
    except Exception as e:
        flash(f"Erreur lors du déchiffrement : {e}", "error")
        return redirect(url_for('list_rapports'))
    finally:
        # Nettoyer le fichier déchiffré
        if os.path.exists(chemin_dechiffre):
            try:
                os.remove(chemin_dechiffre)
            except:
                pass  # Ignorer les erreurs de suppression

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

@app.route("/api/tools")
@require_auth
def api_tools():
    """API pour récupérer la liste des outils disponibles"""
    return json.dumps(AVAILABLE_TOOLS)

@app.route("/debug/reports")
@require_auth
def debug_reports():
    """Page de debug pour les rapports"""
    output = []
    
    # Vérifier le dossier
    output.append(f"Dossier rapports: {RAPPORT_FOLDER}")
    output.append(f"Dossier existe: {os.path.exists(RAPPORT_FOLDER)}")
    
    if os.path.exists(RAPPORT_FOLDER):
        files = list(Path(RAPPORT_FOLDER).glob("*"))
        output.append(f"Nombre de fichiers: {len(files)}")
        
        for f in files:
            output.append(f"  - {f.name} ({f.stat().st_size} bytes)")
            
        # Test des fonctions de formatage
        for f in files[:3]:
            output.append(f"\nTest formatage pour: {f.name}")
            output.append(f"  Outil: {get_tool_name(f.name)}")
            output.append(f"  Date: {format_date(f.name)}")
            output.append(f"  Icône: {get_tool_icon(f.name)}")
    
    return Response("\n".join(output), mimetype='text/plain')

@app.route("/debug/rapports")
@require_auth
def debug_rapports_detailed():
    """Debug détaillé des rapports"""
    output = []
    
    # Informations système
    output.append("=== DEBUG RAPPORTS DÉTAILLÉ ===")
    output.append(f"Heure: {datetime.now()}")
    output.append(f"Dossier de travail: {os.getcwd()}")
    output.append(f"RAPPORT_FOLDER: {RAPPORT_FOLDER}")
    output.append("")
    
    # Vérifier le dossier
    output.append(f"📂 Dossier {RAPPORT_FOLDER}:")
    output.append(f"  Existe: {os.path.exists(RAPPORT_FOLDER)}")
    output.append(f"  Est un dossier: {os.path.isdir(RAPPORT_FOLDER)}")
    
    if os.path.exists(RAPPORT_FOLDER):
        try:
            # Lister tous les fichiers
            rapport_path = Path(RAPPORT_FOLDER)
            all_files = list(rapport_path.glob("*"))
            output.append(f"  Nombre total de fichiers: {len(all_files)}")
            output.append("")
            
            output.append("📋 Tous les fichiers:")
            for f in sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True):
                size = f.stat().st_size
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                output.append(f"  📄 {f.name}")
                output.append(f"     Taille: {size} bytes")
                output.append(f"     Modifié: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                output.append(f"     Outil: {get_tool_name(f.name)}")
                output.append(f"     Date formatée: {format_date(f.name)}")
                output.append("")
            
            # Filtrer les .aes comme dans la fonction list_rapports
            output.append("🔒 Fichiers .aes (logique de l'app):")
            aes_files = list(rapport_path.glob("*.html.aes")) + list(rapport_path.glob("*.aes"))
            output.append(f"  Trouvés: {len(aes_files)} fichiers")
            
            fichiers_affiches = []
            for f in sorted(aes_files, key=lambda x: x.stat().st_mtime, reverse=True):
                if not f.name.startswith('wireshark_'):
                    fichiers_affiches.append(f.name)
                    output.append(f"  ✅ {f.name} (affiché)")
                else:
                    output.append(f"  ❌ {f.name} (exclu - wireshark)")
            
            output.append("")
            output.append(f"📊 Résumé:")
            output.append(f"  Fichiers totaux: {len(all_files)}")
            output.append(f"  Fichiers .aes: {len(aes_files)}")
            output.append(f"  Fichiers affichés: {len(fichiers_affiches)}")
            
            # Test des fonctions de formatage
            output.append("")
            output.append("🧪 Test des fonctions:")
            if fichiers_affiches:
                test_file = fichiers_affiches[0]
                output.append(f"  Fichier test: {test_file}")
                output.append(f"  get_tool_name: {get_tool_name(test_file)}")
                output.append(f"  get_tool_icon: {get_tool_icon(test_file)}")
                output.append(f"  get_tool_color: {get_tool_color(test_file)}")
                output.append(f"  format_date: {format_date(test_file)}")
            
        except Exception as e:
            output.append(f"❌ Erreur lors de l'analyse: {e}")
            output.append(f"Traceback: {traceback.format_exc()}")
    
    # Vérifier la configuration
    output.append("")
    output.append("⚙️ Configuration:")
    output.append(f"  AVAILABLE_TOOLS: {len(AVAILABLE_TOOLS)} outils")
    for tool, info in AVAILABLE_TOOLS.items():
        output.append(f"    {tool}: {info['name']}")
    
    # Test de la session
    output.append("")
    output.append("🔐 Session:")
    output.append(f"  Authentifié: {session.get('authenticated', False)}")
    
    return Response("\n".join(output), mimetype='text/plain')

@app.route("/test/create-report")
@require_auth
def test_create_report():
    """Créer un rapport de test pour vérifier l'affichage"""
    try:
        # Créer le dossier s'il n'existe pas
        os.makedirs(RAPPORT_FOLDER, exist_ok=True)
        
        # Créer un rapport de test
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        test_file = os.path.join(RAPPORT_FOLDER, f"nmap_{date}.html")
        
        test_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport de Test - Nmap</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid #007bff; }}
        .info {{ background-color: #d4edda; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Rapport de Test Nmap</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Cible:</strong> Test Target</p>
        <p><strong>Dossier:</strong> {RAPPORT_FOLDER}</p>
    </div>
    
    <div class="info">
        <h2>ℹ️ Information</h2>
        <p>Ceci est un rapport de test généré automatiquement pour vérifier que l'interface web fonctionne correctement avec le dossier <strong>{RAPPORT_FOLDER}</strong>.</p>
    </div>
    
    <h2>📊 Résultats du Scan</h2>
    <pre>
Starting Nmap 7.91 ( https://nmap.org ) at {datetime.now().strftime('%Y-%m-%d %H:%M')}
Nmap scan report for test-target
Host is up (0.00010s latency).

PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1
80/tcp   open  http    Apache httpd 2.4.41
443/tcp  open  https   Apache httpd 2.4.41

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 2.15 seconds
    </pre>
    
    <h2>🔓 Analyse de Sécurité</h2>
    <div class="info">
        <p><strong>Services détectés:</strong> SSH, HTTP, HTTPS</p>
        <p><strong>Recommandations:</strong> Vérifier les configurations de sécurité</p>
        <p><strong>Fichier généré dans:</strong> {RAPPORT_FOLDER}/</p>
    </div>
</body>
</html>"""
        
        # Écrire le fichier
        with open(test_file, "w", encoding='utf-8') as f:
            f.write(test_content)
        
        # Chiffrer le fichier
        from encrypt import encrypt_file
        encrypt_file(test_file)
        
        flash(f"Rapport de test créé et chiffré: nmap_{date}.html.aes dans {RAPPORT_FOLDER}/", "success")
        return redirect(url_for('list_rapports'))
        
    except Exception as e:
        flash(f"Erreur lors de la création du rapport de test: {e}", "error")
        return redirect(url_for('list_rapports'))

@app.route("/stats")
@require_auth
def stats():
    """Statistiques des rapports"""
    try:
        stats_data = {
            'total_rapports': 0,
            'par_outil': {},
            'derniers_scans': [],
            'taille_totale': 0
        }
        
        if os.path.exists(RAPPORT_FOLDER):
            rapport_path = Path(RAPPORT_FOLDER)
            aes_files = list(rapport_path.glob("*.aes"))
            
            stats_data['total_rapports'] = len(aes_files)
            
            for f in aes_files:
                # Statistiques par outil
                tool_name = get_tool_name(f.name)
                stats_data['par_outil'][tool_name] = stats_data['par_outil'].get(tool_name, 0) + 1
                
                # Taille totale
                stats_data['taille_totale'] += f.stat().st_size
                
                # Derniers scans (5 plus récents)
                if len(stats_data['derniers_scans']) < 5:
                    stats_data['derniers_scans'].append({
                        'nom': f.name,
                        'outil': tool_name,
                        'date': format_date(f.name),
                        'taille': f.stat().st_size
                    })
            
            # Trier les derniers scans par date de modification
            aes_files_sorted = sorted(aes_files, key=lambda x: x.stat().st_mtime, reverse=True)
            stats_data['derniers_scans'] = []
            for f in aes_files_sorted[:5]:
                stats_data['derniers_scans'].append({
                    'nom': f.name,
                    'outil': get_tool_name(f.name),
                    'date': format_date(f.name),
                    'taille': f.stat().st_size
                })
        
        return render_template("stats.html", stats=stats_data)
        
    except Exception as e:
        flash(f"Erreur lors du calcul des statistiques: {e}", "error")
        return redirect(url_for('index'))

if __name__ == "__main__":
    # Créer les dossiers nécessaires
    os.makedirs(RAPPORT_FOLDER, exist_ok=True)
    os.makedirs(TOOLS_FOLDER, exist_ok=True)
    
    # Vérifier la présence des scripts
    missing_scripts = []
    for tool_key, tool_info in AVAILABLE_TOOLS.items():
        script_path = os.path.join(TOOLS_FOLDER, tool_info['script'])
        if not os.path.isfile(script_path):
            missing_scripts.append(tool_info['script'])
    
    if missing_scripts:
        print("⚠️  Scripts manquants dans le dossier tools/:")
        for script in missing_scripts:
            print(f"   - {script}")
        print()
    
    print(f"🚀 Serveur démarré avec {len(AVAILABLE_TOOLS)} outils disponibles")
    print(f"📁 Dossier outils: {TOOLS_FOLDER}")
    print(f"📁 Dossier rapports: {RAPPORT_FOLDER}")
    print(f"🔧 Routes de debug disponibles:")
    print(f"   - /debug/reports")
    print(f"   - /debug/rapports")
    print(f"   - /test/create-report")
    print(f"   - /stats")
    print(f"🌐 Interface accessible sur: http://localhost:5000")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
