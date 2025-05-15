import sys
import socket
#import scapy.all as scapy (J'ai enlever la librairie pour l'instant car j'ai quelque bug a gérer avec le rest)
from datetime import datetime

#Choice of the module to use
module=0
while(module<1 or module>5):
    module =input(("Choose module \n 1-SOC \n 2-SaaS \n 3-Infrastructure \n 4-Client Support \n 5- HR \n"))
    module=int(module)
5
if module==1:
    print("1 SOC")
    #=================================SOC,EDR,XDR=================================
    #Begin
    #===============NMAP===============
    #Begin
    target = input(str("Target IP: "))
    with open("demofile.txt", "w") as f:
        f.write("1 SOC")
        f.write("Target IP: ",target)
    try:
        #Scan de tout les ports de la cible
        for port in range(1,65535):
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            socket.setdefaulttimeout(0.5)
            #Return open port
            result = s.connect_ex((target,port))
            f.write("\n")
        if result == 0:
            print("[*] Port {} is open".format(port))
            f.write("[*] Port {} is open".format(port))
        s.close()
    except KeyboardInterrupt:
        print("\n Exoiteng :")
    except socket.error:
        print("\ Host not respond")
        sys.exit()
    #End
    #===============NMAP===============
    #===============Metasploit===============
    #Begin
    #End
    #===============Metasploit===============*
        #Fait avec SCAPY garder hors main pour l'instat
    #===============Wireshark===============
    #Begin
    #End
    #===============Wireshark===============

    #===============OWASP_ZAP===============
    #Begin
    #End
    #===============OWASP_ZAP===============

    #End
    #=================================SOC,EDR,XDR=================================


if module==2:
    print("2 SaaS")
    with open("demofile.txt", "w") as f:
        f.write("2 SaaS")
    #=================================SaaS=================================
    #Begin

    #===============BURP SUITE===============
    #Begin
    #End
    #===============BURP SUITE===============

    #===============Postman===============
    #Begin
    #End
    #===============Postman===============

    #===============SQLmap===============
    #Begin
    #End
    #===============SQLmap===============

    #===============OWASP===============
    #Begin
    #End
    #===============OWASP===============

    #End
    #=================================SaaS=================================

if module==3:
    print("3 Infrastructure")
    with open("demofile.txt", "w") as f:
        f.write("3 Infrastructure")
    #=================================Infrastructure=================================
    #Begin

    #===============OpenVAS===============
    #Begin
    #End
    #===============OpenVAS===============

    #===============Nessus===============
    #Begin
    #End
    #===============Nessus===============

    #===============Hydra===============
    #Begin
    #End
    #===============Hydra===============

    #===============Aircrak-ng===============
    #Begin
    #End
    #===============Aircrak-ng===============

    #End
    #=================================Infrastructure=================================

if module==4:
    print("4 Client Support")
    with open("demofile.txt", "w") as f:
        f.write("4 Client Support")
    #=================================Client Support=================================
    #Begin

    #===============Nikto===============
    #Begin
    #End
    #===============Nikto===============

    #===============SSLyze===============
    #Begin
    #End
    #===============SSLyze===============

    #===============Ettercap===============
    #Begin
    #End
    #===============Ettercap===============

    #===============Maltego===============
    #Begin
    #End
    #===============Maltego===============

    #End
    #=================================Client Support=================================

if module==5:
    print("5 HR")
    with open("demofile.txt", "w") as f:
        f.write("5 HR")
    #=================================HR=================================
    #Begin

    #===============John the Ripper===============
    #Begin
    #End
    #===============John the Ripper===============

    #===============Cain & Abel===============
    #Begin
    #End
    #===============Cain & Abel===============

    #===============Acunetix===============
    #Begin
    #End
    #===============Acunetix===============

    #===============NSE===============
    #Begin
    #End
    #===============NSE===============

    #End
    #=================================HR=================================
