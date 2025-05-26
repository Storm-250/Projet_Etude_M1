import sys
import socket
import nmap
#import scapy.all as scapy (J'ai enlever la librairie pour l'instant car j'ai quelque bug a gérer avec le rest)
from datetime import datetime

#Choice of the module to use
module=0
while(module<1 or module>5):
    module =input(("Choose module \n 1-SOC \n 2-SaaS \n 3-Infrastructure \n 4-Client Support \n 5- HR \n"))
    module=int(module)
if module==1:
    print("1 SOC")
    #=================================SOC,EDR,XDR=================================
    #Begin
    #===============NMAP===============
    #Begin
    scanner = nmap.PortScanner()
    print("Welcome, this is a simple nmap automation tool")
    print("<----------------------------------------------------->")
    
    ip_addr = input("Please enter the IP address you want to scan: ")
    print("The IP you entered is: ", ip_addr)
    type(ip_addr)
    
    resp = input("""\nPlease enter the type of scan you want to run
                    1)SYN ACK Scan
                    2)UDP Scan
                    3)Comprehensive Scan \n""")
    print("You have selected option: ", resp)
    resp_dict={'1':['-v -sS','tcp'],'2':['-v -sU','udp'],'3':['-v -sS -sV -sC -A -O','tcp']}
    if resp not in resp_dict.keys():
        print("enter a valid option")
    else:
        print("nmap version: "sccaner.nmap_version())
        scanner.scan(ip_addr,"1-1024",resp_dict[resp][0]) #the # are port range to scan, the last part is the scan type
        print(scanner.scaninfo())
        if scanner.scaninfo()=='up':
            print("Scanner Status: ",scanner[ip_addr].state())
            print(scanner[ip_addr].all_protocols())
            print("Open Ports: ",scanner[ip_addr][resp_dict[resp][1]].keys())  #display all open ports
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
