import sys
import requests
import ssl
import socket
from datetime import datetime
from encrypt import encrypt_file
import os
from urllib.parse import urlparse
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: https_test.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # S'assurer que le dossier rapports existe
    rapports_dir = "rapports"
    if not os.path.exists(rapports_dir):
        os.makedirs(rapports_dir)
        print(f"📁 Dossier {rapports_dir} créé")
    
    # Format de nom correct pour l'interface web
    html_path = os.path.join(rapports_dir, f"https_test_{date}.html")
    
    print(f"🔍 Test HTTPS/SSL en cours sur {target}...")
    print(f"📄 Fichier de sortie: {html_path}")

    # Tests à effectuer
    test_results = {}
    
    # 1. Test de connectivité HTTPS
    print("🔐 Test de connectivité HTTPS...")
    test_results['https_connectivity'] = test_https_connectivity(target)
    
    # 2. Test des certificats SSL
    print("📋 Analyse du certificat SSL...")
    test_results['ssl_certificate'] = test_ssl_certificate(target)
    
    # 3. Test des en-têtes de sécurité
    print("🛡️ Test des en-têtes de sécurité...")
    test_results['security_headers'] = test_security_headers(target)
    
    # 4. Test des protocoles SSL/TLS
    print("🔒 Test des protocoles SSL/TLS...")
    test_results['ssl_protocols'] = test_ssl_protocols(target)
    
    # 5. Test des ciphers
    print("🔑 Test des algorithmes de chiffrement...")
    test_results['ssl_ciphers'] = test_ssl_ciphers(target)

    # Générer le rapport HTML
    try:
        with open(html_path, "w", encoding='utf-8') as f:
            # Calculer le score de sécurité global
            security_score = calculate_security_score(test_results)
            
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport HTTPS/SSL - {target}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .info {{ background-color: #ebf7fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .success {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .error {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 0 5px 5px 0; }}
        .test-section {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #6c757d; }}
        .test-pass {{ border-left-color: #28a745; }}
        .test-fail {{ border-left-color: #dc3545; }}
        .test-warn {{ border-left-color: #ffc107; }}
        .score {{ font-size: 2em; font-weight: bold; text-align: center; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .score-excellent {{ background-color: #d4edda; color: #155724; }}
        .score-good {{ background-color: #d1ecf1; color: #0c5460; }}
        .score-average {{ background-color: #fff3cd; color: #856404; }}
        .score-poor {{ background-color: #f8d7da; color: #721c24; }}
        .cert-info {{ background-color: white; padding: 10px; margin: 10px 0; border-left: 3px solid #17a2b8; border-radius: 0 5px 5px 0; }}
        .header-check {{ display: flex; justify-content: space-between; align-items: center; padding: 8px; margin: 5px 0; border-radius: 3px; }}
        .header-present {{ background-color: #d4edda; }}
        .header-missing {{ background-color: #f8d7da; }}
        .protocol-item {{ display: inline-block; padding: 5px 10px; margin: 5px; border-radius: 15px; color: white; font-weight: bold; }}
        .protocol-secure {{ background-color: #28a745; }}
        .protocol-deprecated {{ background-color: #dc3545; }}
        .protocol-warning {{ background-color: #ffc107; color: black; }}
        pre {{ background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Rapport HTTPS/SSL - Analyse de Sécurité</h1>
        <div class="info">
            <strong>🎯 Cible:</strong> {target}<br>
            <strong>📅 Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>🔧 Type de test:</strong> Analyse HTTPS/SSL/TLS<br>
            <strong>🏆 Score de sécurité:</strong> {security_score}/100
        </div>""")

            # Afficher le score global
            if security_score >= 90:
                score_class = "score-excellent"
                score_text = "Excellent"
            elif security_score >= 75:
                score_class = "score-good"
                score_text = "Bon"
            elif security_score >= 50:
                score_class = "score-average"
                score_text = "Moyen"
            else:
                score_class = "score-poor"
                score_text = "Insuffisant"

            f.write(f'<div class="score {score_class}">Score SSL/TLS: {security_score}/100 - {score_text}</div>')

            # Section connectivité HTTPS
            connectivity = test_results['https_connectivity']
            section_class = "test-pass" if connectivity['success'] else "test-fail"
            f.write(f"""
        <div class="test-section {section_class}">
            <h3>🌐 Connectivité HTTPS</h3>
            <p><strong>Statut:</strong> {'✅ Succès' if connectivity['success'] else '❌ Échec'}</p>
            <p><strong>URL testée:</strong> {connectivity['url']}</p>
            <p><strong>Code de statut:</strong> {connectivity.get('status_code', 'N/A')}</p>
            <p><strong>Temps de réponse:</strong> {connectivity.get('response_time', 'N/A')}</p>
            {f"<p><strong>Erreur:</strong> {connectivity['error']}</p>" if connectivity.get('error') else ''}
        </div>""")

            # Section certificat SSL
            cert = test_results['ssl_certificate']
            if cert['success']:
                cert_class = "test-pass"
                cert_status = "✅ Certificat valide"
            elif cert.get('expired'):
                cert_class = "test-fail"
                cert_status = "❌ Certificat expiré"
            else:
                cert_class = "test-fail"
                cert_status = "❌ Problème de certificat"

            f.write(f"""
        <div class="test-section {cert_class}">
            <h3>📋 Certificat SSL</h3>
            <p><strong>Statut:</strong> {cert_status}</p>""")

            if cert.get('cert_info'):
                info = cert['cert_info']
                f.write(f"""
            <div class="cert-info">
                <strong>Sujet:</strong> {info.get('subject', 'N/A')}<br>
                <strong>Émetteur:</strong> {info.get('issuer', 'N/A')}<br>
                <strong>Valide du:</strong> {info.get('not_before', 'N/A')}<br>
                <strong>Valide jusqu'au:</strong> {info.get('not_after', 'N/A')}<br>
                <strong>Algorithme de signature:</strong> {info.get('signature_algorithm', 'N/A')}<br>
                <strong>Version:</strong> {info.get('version', 'N/A')}
            </div>""")

            if cert.get('error'):
                f.write(f"<p><strong>Erreur:</strong> {cert['error']}</p>")

            f.write('</div>')

            # Section en-têtes de sécurité
            headers = test_results['security_headers']
            headers_class = "test-pass" if headers['score'] >= 70 else ("test-warn" if headers['score'] >= 40 else "test-fail")
            
            f.write(f"""
        <div class="test-section {headers_class}">
            <h3>🛡️ En-têtes de Sécurité</h3>
            <p><strong>Score:</strong> {headers['score']}/100</p>""")

            important_headers = {
                'Strict-Transport-Security': 'Force HTTPS pour le domaine',
                'Content-Security-Policy': 'Prévient les attaques XSS',
                'X-Frame-Options': 'Prévient le clickjacking',
                'X-Content-Type-Options': 'Prévient le MIME sniffing',
                'Referrer-Policy': 'Contrôle les informations de référent',
                'Permissions-Policy': 'Contrôle les permissions du navigateur'
            }

            for header, description in important_headers.items():
                is_present = header in headers.get('headers', {})
                header_class = "header-present" if is_present else "header-missing"
                status_icon = "✅" if is_present else "❌"
                f.write(f'<div class="header-check {header_class}"><span>{status_icon} {header}</span><span>{description}</span></div>')

            f.write('</div>')

            # Section protocoles SSL/TLS
            protocols = test_results['ssl_protocols']
            f.write("""
        <div class="test-section">
            <h3>🔒 Protocoles SSL/TLS Supportés</h3>""")

            protocol_info = {
                'TLSv1.3': {'secure': True, 'desc': 'Le plus récent et sécurisé'},
                'TLSv1.2': {'secure': True, 'desc': 'Sécurisé et largement supporté'},
                'TLSv1.1': {'secure': False, 'desc': 'Déprécié, non recommandé'},
                'TLSv1.0': {'secure': False, 'desc': 'Déprécié, vulnérable'},
                'SSLv3': {'secure': False, 'desc': 'Obsolète, très vulnérable'},
                'SSLv2': {'secure': False, 'desc': 'Obsolète, très vulnérable'}
            }

            for protocol, info in protocol_info.items():
                is_supported = protocol in protocols.get('supported', [])
                if is_supported:
                    if info['secure']:
                        protocol_class = "protocol-secure"
                    else:
                        protocol_class = "protocol-deprecated"
                    f.write(f'<span class="protocol-item {protocol_class}">{protocol} - {info["desc"]}</span>')

            if protocols.get('error'):
                f.write(f"<p><strong>Erreur lors du test:</strong> {protocols['error']}</p>")

            f.write('</div>')

            # Section recommandations
            f.write("""
        <h2>🛠️ Recommandations de Sécurité</h2>
        <div class="info">
            <h3>💡 Actions Prioritaires</h3>
            <ul>""")

            # Recommandations basées sur les résultats
            if not connectivity['success']:
                f.write('<li><strong>🚨 Critique:</strong> Activez HTTPS sur votre serveur</li>')
            
            if cert.get('expired'):
                f.write('<li><strong>🚨 Critique:</strong> Renouvelez votre certificat SSL expiré</li>')
            elif not cert['success']:
                f.write('<li><strong>🚨 Critique:</strong> Corrigez les problèmes de certificat SSL</li>')

            if headers['score'] < 70:
                f.write('<li><strong>⚠️ Important:</strong> Configurez les en-têtes de sécurité manquants</li>')

            if 'TLSv1.0' in protocols.get('supported', []) or 'TLSv1.1' in protocols.get('supported', []):
                f.write('<li><strong>⚠️ Important:</strong> Désactivez les protocoles TLS obsolètes (1.0, 1.1)</li>')

            f.write("""
                <li><strong>Configuration recommandée:</strong> TLS 1.2 et 1.3 uniquement</li>
                <li><strong>Certificats:</strong> Utilisez des certificats avec des clés >= 2048 bits</li>
                <li><strong>HSTS:</strong> Implémentez HTTP Strict Transport Security</li>
                <li><strong>Tests réguliers:</strong> Vérifiez périodiquement votre configuration SSL</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>🔗 Outils de Test Recommandés</h3>
            <ul>
                <li><a href="https://www.ssllabs.com/ssltest/">SSL Labs SSL Test</a> - Test complet en ligne</li>
                <li><a href="https://securityheaders.com/">Security Headers</a> - Vérification des en-têtes</li>
                <li><a href="https://testssl.sh/">testssl.sh</a> - Outil en ligne de commande complet</li>
                <li><a href="https://observatory.mozilla.org/">Mozilla Observatory</a> - Audit de sécurité global</li>
            </ul>
        </div>""")

            # Résultats détaillés en accordéon
            f.write("""
        <h2>📊 Résultats Détaillés</h2>
        <details>
            <summary>Voir tous les résultats de tests</summary>
            <pre>""")
            
            for test_name, result in test_results.items():
                f.write(f"\n=== {test_name.upper()} ===\n")
                f.write(f"{result}\n")
            
            f.write("""</pre>
        </details>
    </div>
</body>
</html>""")
        
        print(f"✅ Rapport généré: {html_path}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return

    # Chiffrement
    try:
        if not os.path.exists(html_path) or os.path.getsize(html_path) == 0:
            print(f"❌ Fichier {html_path} invalide pour chiffrement")
            return
            
        print("🔒 Chiffrement en cours...")
        encrypt_file(html_path)
        
        encrypted_path = html_path + ".aes"
        if os.path.exists(encrypted_path):
            encrypted_size = os.path.getsize(encrypted_path)
            print(f"✅ Fichier chiffré: {encrypted_path} ({encrypted_size} bytes)")
        else:
            print("❌ Le fichier chiffré n'a pas été créé")
        
    except Exception as e:
        print(f"❌ Erreur lors du chiffrement: {e}")

def test_https_connectivity(target):
    """Test la connectivité HTTPS de base"""
    result = {'success': False}
    
    # Essayer différentes URLs
    urls_to_test = [
        f"https://{target}",
        f"https://{target}:443",
        f"https://www.{target}" if not target.startswith('www.') else f"https://{target}"
    ]
    
    for url in urls_to_test:
        try:
            result['url'] = url
            start_time = datetime.now()
            
            response = requests.get(url, timeout=10, verify=True)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            result.update({
                'success': True,
                'status_code': response.status_code,
                'response_time': f"{response_time:.2f}s",
                'headers': dict(response.headers)
            })
            break
            
        except requests.exceptions.SSLError as e:
            result['error'] = f"Erreur SSL: {str(e)}"
        except requests.exceptions.ConnectionError as e:
            result['error'] = f"Erreur de connexion: {str(e)}"
        except requests.exceptions.Timeout:
            result['error'] = "Timeout de connexion"
        except Exception as e:
            result['error'] = f"Erreur: {str(e)}"
    
    return result

def test_ssl_certificate(target):
    """Test et analyse du certificat SSL"""
    result = {'success': False}
    
    try:
        # Extraire le hostname et le port
        if ':' in target:
            hostname, port = target.split(':')
            port = int(port)
        else:
            hostname = target
            port = 443
        
        # Créer un contexte SSL
        context = ssl.create_default_context()
        
        # Connexion SSL
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                result['success'] = True
                result['cert_info'] = {
                    'subject': dict(x[0] for x in cert['subject'])['commonName'],
                    'issuer': dict(x[0] for x in cert['issuer'])['commonName'],
                    'not_before': cert['notBefore'],
                    'not_after': cert['notAfter'],
                    'version': cert['version'],
                    'signature_algorithm': cert.get('signatureAlgorithm', 'Unknown')
                }
                
                # Vérifier si le certificat est expiré
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                if not_after < datetime.now():
                    result['expired'] = True
                    result['success'] = False
                
    except ssl.SSLError as e:
        result['error'] = f"Erreur SSL: {str(e)}"
    except socket.timeout:
        result['error'] = "Timeout de connexion SSL"
    except Exception as e:
        result['error'] = f"Erreur: {str(e)}"
    
    return result

def test_security_headers(target):
    """Test les en-têtes de sécurité HTTP"""
    result = {'score': 0, 'headers': {}}
    
    try:
        url = f"https://{target}"
        response = requests.get(url, timeout=10, verify=False)
        headers = response.headers
        
        result['headers'] = dict(headers)
        
        # Score basé sur la présence d'en-têtes importants
        security_headers = {
            'Strict-Transport-Security': 25,
            'Content-Security-Policy': 20,
            'X-Frame-Options': 15,
            'X-Content-Type-Options': 15,
            'Referrer-Policy': 10,
            'Permissions-Policy': 10,
            'X-XSS-Protection': 5
        }
        
        score = 0
        for header, points in security_headers.items():
            if header in headers:
                score += points
        
        result['score'] = score
        
    except Exception as e:
        result['error'] = f"Erreur: {str(e)}"
    
    return result

def test_ssl_protocols(target):
    """Test les protocoles SSL/TLS supportés"""
    result = {'supported': []}
    
    try:
        hostname = target.split(':')[0]
        port = int(target.split(':')[1]) if ':' in target else 443
        
        protocols_to_test = [
            ('TLSv1.3', ssl.PROTOCOL_TLS),
            ('TLSv1.2', ssl.PROTOCOL_TLS),
            ('TLSv1.1', ssl.PROTOCOL_TLS),
            ('TLSv1.0', ssl.PROTOCOL_TLS)
        ]
        
        supported = []
        
        for protocol_name, protocol_const in protocols_to_test:
            try:
                context = ssl.SSLContext(protocol_const)
                
                # Configurer selon le protocole
                if protocol_name == 'TLSv1.3':
                    context.minimum_version = ssl.TLSVersion.TLSv1_3
                    context.maximum_version = ssl.TLSVersion.TLSv1_3
                elif protocol_name == 'TLSv1.2':
                    context.minimum_version = ssl.TLSVersion.TLSv1_2
                    context.maximum_version = ssl.TLSVersion.TLSv1_2
                elif protocol_name == 'TLSv1.1':
                    context.minimum_version = ssl.TLSVersion.TLSv1_1
                    context.maximum_version = ssl.TLSVersion.TLSv1_1
                elif protocol_name == 'TLSv1.0':
                    context.minimum_version = ssl.TLSVersion.TLSv1
                    context.maximum_version = ssl.TLSVersion.TLSv1
                
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        supported.append(protocol_name)
                        
            except (ssl.SSLError, OSError, socket.error):
                # Protocole non supporté
                pass
            except Exception:
                # Autre erreur, ignorer
                pass
        
        result['supported'] = supported
        
    except Exception as e:
        result['error'] = f"Erreur: {str(e)}"
    
    return result

def test_ssl_ciphers(target):
    """Test les algorithmes de chiffrement supportés"""
    result = {'ciphers': []}
    
    try:
        # Utilisation d'OpenSSL si disponible
        hostname = target.split(':')[0]
        port = target.split(':')[1] if ':' in target else '443'
        
        try:
            cmd = f"openssl s_client -connect {hostname}:{port} -cipher ALL < /dev/null 2>/dev/null | grep 'Cipher    :'"
            cipher_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if cipher_result.returncode == 0 and cipher_result.stdout:
                cipher_line = cipher_result.stdout.strip()
                if 'Cipher    :' in cipher_line:
                    cipher = cipher_line.split('Cipher    :')[1].strip()
                    result['ciphers'] = [cipher]
            
        except subprocess.TimeoutExpired:
            result['error'] = "Timeout lors du test des ciphers"
        except FileNotFoundError:
            result['error'] = "OpenSSL non disponible"
        except Exception as e:
            result['error'] = f"Erreur: {str(e)}"
            
    except Exception as e:
        result['error'] = f"Erreur: {str(e)}"
    
    return result

def calculate_security_score(test_results):
    """Calcule un score de sécurité global"""
    score = 0
    
    # Connectivité HTTPS (20 points)
    if test_results['https_connectivity']['success']:
        score += 20
    
    # Certificat SSL (30 points)
    if test_results['ssl_certificate']['success']:
        score += 30
    elif test_results['ssl_certificate'].get('expired'):
        score += 10  # Certificat présent mais expiré
    
    # En-têtes de sécurité (30 points)
    headers_score = test_results['security_headers']['score']
    score += int(headers_score * 0.3)  # Convertir le score /100 en /30
    
    # Protocoles SSL (20 points)
    protocols = test_results['ssl_protocols'].get('supported', [])
    if 'TLSv1.3' in protocols:
        score += 10
    if 'TLSv1.2' in protocols:
        score += 10
    if 'TLSv1.1' in protocols or 'TLSv1.0' in protocols:
        score -= 10  # Pénalité pour les anciens protocoles
    
    return max(0, min(100, score))  # Score entre 0 et 100

if __name__ == "__main__":
    main()