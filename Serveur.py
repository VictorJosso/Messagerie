# -*- coding: utf-8 -*-
"""Code par Victor Josso"""
from __future__ import unicode_literals
import socket
import select
import time
import sys
import datetime
import threading
import random
import os
import binascii
import time
import hashlib
import argparse

version  = "1.0"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Serveur pour la messagerie, par Victor Josso")
    parser.add_argument("-p", "--port", help="Définissez le port sur lequel écouter (default : "+str(port)+")")

    return parser.parse_args()

def log(text):
    log = open("log.txt", "a")
    log.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"]"+text+"\n")
    log.close()

def verif_path(path):
    if not os.path.exists(path):
        original_path = os.getcwd()
        for x in path.split("/")[:len(path.split("/"))-1]:
            try:
                os.mkdir(x)
            except OSError as error:
                pass
            os.chdir(x)
        os.chdir(original_path)
        os.mknod(path)
    else:
        pass


class Client:
    """
    Cette classe contient toutes les informations du client connecté (informations de connexion, username, id, amis, etc...).
    Elle gère l'envoi de message au client en question, la reception des messages envoyé par lui, et sa déconnexion forcée.
    """
    def __init__(self,connection, infos):
        self.connection = connection
        self.infos = infos
        self.username = None
        self.id_client = None
        self.logged_in = False
        self.friends = []
        self.properties = ""
        self.forcedisconnected = False
        self.releve = ""
        self.data_file = None

    def send(self,message):
        """
        Envoie un message au client.
        """
        self.connection.send(message)
    def recv(self, lenth):
        """
        Recoit les messages du client.
        """
        return self.connection.recv(lenth)
    def disconnect(self, reason):
        """
        Déconnecte le client de force et enregistre la raison.
        """
        self.connection.close()
        log("Le client "+str(self.infos)+" a ete deconnecte pour la raison suivante : "+reason)
        self.forcedisconnected = True

hote = ""
port = 26281

args = parse_arguments()

if args.port:
    try:
        port = int(args.port)
        if not (port >= 1 and port <= 65535):
            raise ValueError
    except:
        print "Le port sur lequel écouter doit être un nombre entier compris entre 1 et 65535"
        sys.exit()



connection_principale = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection_principale.bind((hote, port))
connection_principale.listen(5)

verrou = threading.RLock()
class Accepter_client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            self.co_demandees, self.wlist, self.xlist = select.select([connection_principale], [], [], 0.05)
            for co in self.co_demandees :
                self.co_avec_client, self.infos = co.accept()
                self.client = Client(self.co_avec_client, self.infos)
                clients.append(self.client)
                releve = Releve(self.client)
                releve.setName("Client not logged in")
                self.client.releve = releve
                releve.start()
                log("Nouveau client connecte : "+str(self.infos))
            if os.path.exists("shutdown"):
                self.f = open("shutdown","r")
                self.verif = self.f.read()
                self.f.close()
                self.verif = hashlib.sha512(self.verif.encode()).hexdigest()
                if len(self.verif) == 0:
                    self.verif = None
                if self.verif == "9c337aa05d1a55fb153c910c3db04c2717f7f030167ba83e06f9b14934e073d4ddbdf90f0a82ed6e3505b86f85eb6796da436f83bf7ea7a3284cfc9cd2ed6ea4":
                    print "Arret en cours..."
                    os.remove("shutdown")
                    log("L'arret du server a ete demande. La signature a ete verifiee. Le server va s'arreter.")
                    for self.x in clients :
                        self.x.send("SERVER\\SHUTDOWN")
                        self.x.releve.has_to_stop = True
                        self.x.disconnect("Server shutdown")
                        print "Il y a "+str(len(threading.enumerate()))+" threads."
                    for self.x in threading.enumerate():
                        if not self.x == threading.currentThread():
                            self.x.join(1)
                            print "Etat du thread "+str(self.x)+" : "+str(self.x.isAlive())
                    sys.exit()
                else:
                    os.remove("shutdown")
                    log("L'arret du server a ete demande. La signature n'a pas pu etre verifiee. DEMANDE INGOREE. (key : "+str(self.verif)+")")




verrou_bis = threading.RLock()
class Releve(threading.Thread):
    def __init__(self, client):
        self.client = client
        threading.Thread.__init__(self)
        self.has_to_stop = False

    def run(self):
        self.msgs_rcved = []
        while not self.has_to_stop:
            try:
                try:
                    self.msg_recu = self.client.recv(33554432)
                    self.msgs_rcved.append(self.msg_recu)
                except socket.error:
                    if not self.client.forcedisconnected:
                        log("Le client "+str(self.client.infos)+" s'est deconnecte.")
                    clients.remove(self.client)
                    break
                if self.msg_recu.split("\\")[0] == "ASKQUITTING":
                    self.client.send("OK")
                    log("Le client "+str(self.client.infos)+" s'est deconnecte.")
                    clients.remove(self.client)
                    break
                elif self.msg_recu.split("\\")[0] == "OK":
                    pass
                elif self.msg_recu.split("\\")[0] == "CONNECT":
                    try :
                        self.f = open("clients/datas/"+"/".join(self.msg_recu.split("\\")[1:]),"r")
                        self.client.send("CONNECT\\OK")
                        self.infos_client = self.f.read()
                        self.client.id_client = self.infos_client.split("\n")[3].split(" = ")[1]
                        self.client.username = self.infos_client.split("\n")[0].split(" = ")[1]
                        self.client.friends = self.infos_client.split("\n")[4].split(" = ")[1].split(", ")
                        self.client.logged_in = True
                        self.client.properties = self.infos_client.split("\n")
                        self.client.data_file = "clients/datas/"+"/".join(self.msg_recu.split("\\")[1:])
                        self.f.close()
                        threading.currentThread().setName(self.client.username)
                        log("Client "+str(self.client.infos)+" connecte en tant que "+str(self.client.username)+" id "+str(self.client.id_client))
                    except IOError:
                        self.client.send("CONNECT\\FAILED")
                elif self.msg_recu.split("\\")[0]=="REGISTER" and len(self.msg_recu.split("\\")) == 4:
                    verif_path("clients/convert-tables/users")
                    verif_path("clients/convert-tables/mails")
                    self.users = open(str("clients/convert-tables/users"),'r').read().split("\n")
                    self.mails = open("clients/convert-tables/mails",'r').read().split("\n")
                    if not self.msg_recu.split("\\")[1] in self.users:
                        if not self.msg_recu.split("\\")[3] in self.mails:
                            try:
                                os.system("python add\ user.py -u "+self.msg_recu.split("\\")[1]+" -s "+self.msg_recu.split('\\')[2]+" -e "+self.msg_recu.split("\\")[3])
                                self.client.send("REGISTER\\OK")
                            except:
                                self.client.send("REGISTER\\ERROR")
                        else:
                            self.client.send("REGISTER\\EMAIL_ALREADY_USED")
                    else:
                        self.client.send("REGISTER\\USERNAME_ALREADY_EXISTS")
                elif self.msg_recu.split("\\")[0]=="GET" and len(self.msg_recu.split("\\")) > 1:
                    if self.msg_recu.split("\\")[1]=="friends":
                        if self.client.logged_in:
                            self.client.send(", ".join(self.client.friends))
                            log("Demande des amis de "+self.client.username+".")
                        else :
                            self.client.send("GET\\friends\\REFUSED")
                            log("Le client "+str(self.client.infos)+" a demande ses amis alors qu'il n'etait pas connecte. Son acces a ete refuse. Il va etre deconnecte.")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)
                    elif self.msg_recu.split("\\")[1] == "unreaded":
                        if self.client.logged_in:
                            if len(self.msg_recu.split("\\"))==2:
                                self.files = os.listdir("clients"+os.sep+"messages"+os.sep+self.client.username)
                                """print self.dir_contains
                                self.files = []
                                for x in self.dir_contains:
                                    if os.path.isfile(x):
                                        self.files.append(x)"""
                                self.client.send("GIVE\\unreaded\\"+str(len(self.files)))
                            elif len(self.msg_recu.split("\\"))==3:
                                self.conv_name = self.files[int(self.msg_recu.split("\\")[2])]
                                if os.path.exists("clients/Keys/"+self.client.username+"/"+self.conv_name+"key"):
                                    verif_path("clients/Keys/"+self.client.username+"/"+self.conv_name+"key")
                                    self.key = open("clients/Keys/"+self.client.username+"/"+self.conv_name+"key","r")
                                    self.client.send("KEY\\"+self.conv_name+"\\"+self.key.read())
                                    self.key.close()
                                    os.remove("clients/Keys/"+self.client.username+"/"+self.conv_name+"key")
                                    #time.sleep(1)
                                verif_path("clients/messages/"+self.client.username+"/"+self.conv_name)
                                self.conv = open("clients/messages/"+self.client.username+"/"+self.conv_name, "r").read()
                                self.client.send("GIVE\\unreaded\\"+self.conv_name+"\\"+self.conv)
                                os.remove("clients/messages/"+self.client.username+"/"+self.conv_name)
                        else :
                            self.client.send("GET\\unreaded\\REFUSED")
                            log("Le client "+str(self.client.infos)+" a demande ses messages non lus alors qu'il n'etait pas connecte. Son acces a ete refuse. Il va etre deconnecte.")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)
                    elif self.msg_recu.split("\\")[1] == "backup":
                        if self.client.logged_in:
                            if os.path.exists("clients/Backups/"+self.client.username+"/backup.zip"):
                                self.bkp_to_send_file = open("clients/Backups/"+self.client.username+"/backup.zip", "rb")
                                self.bkp_to_send = self.bkp_to_send_file.read()
                                self.bkp_to_send_file.close()
                                self.bkp_to_send = binascii.hexlify(self.bkp_to_send)
                                self.client.send("GIVE\\backup\\OK\\"+self.bkp_to_send)
                            else:
                                self.client.send("GIVE\\backup\\UNABLE")
                        else:
                            self.client.send("GET\\REFUSED")
                            log("Le client "+str(self.client.infos)+" a demande une sauvegarde sans etre connecte. Son acces a ete refuse. Il va etre deconnecte.")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "SEND" and len(self.msg_recu.split("\\")) > 2:
                    if self.client.logged_in:
                        verif_path("clients/messages/"+self.msg_recu.split("\\")[1]+"/"+self.client.username)
                        self.f = open("clients/messages/"+self.msg_recu.split("\\")[1]+"/"+self.client.username,"a")
                        self.f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+self.client.username+"]"+self.msg_recu.split("\\")[2]+"\n")
                        self.f.close()
                        self.client.send("SEND\\OK")
                    else :
                        self.client.send("SEND\\REFUSED")
                        log("Le client "+str(self.client.infos)+" a tente d'envoyer un message a "+self.msg_recu.split("\\")[1]+" alors qu'il n'etait pas connecte. Son acces a ete refuse. Il va etre deconnecte.")
                        self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "ADD" and len(self.msg_recu.split("\\")) > 1:
                    if self.msg_recu.split("\\")[1] == "friend" and len(self.msg_recu.split("\\")) > 2:
                        if self.client.logged_in:
                            verif_path("clients/convert-tables/users")
                            self.users = open("clients/convert-tables/users",'r').read().split("\n")
                            if "\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]) in self.users:
                                self.client.friends.append("\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]))
                                self.client.properties[4] = self.client.properties[4].split(" = ")
                                self.client.properties[4][1] = self.client.properties[4][1].split(", ")
                                self.client.properties[4][1].append("\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]))
                                self.client.properties[4][1] = ", ".join(self.client.properties[4][1])
                                self.client.properties[4] = " = ".join(self.client.properties[4])
                                self.f = open(self.client.data_file,"w")
                                self.f.write("\n".join(self.client.properties))
                                self.f.close()
                                self.client.send("ADD\\friend\\OK")
                            else :
                                self.client.send("ADD\\friend\\404")
                        else:
                            self.client.send("ADD\\friend\\REFUSED")
                            log("Le client "+str(self.client.infos)+" a tente d'ajouter un ami alors qu'il n'etait pas connecte. Son acces a ete refuse. Il va etre deconnecte.")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "REMOVE" and len(self.msg_recu.split("\\")) > 1:
                    if self.msg_recu.split("\\")[1] == "friend" and len(self.msg_recu.split("\\")) > 2:
                        if self.client.logged_in:
                            if "\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]) in self.client.friends:
                                self.client.friends.remove("\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]))
                                self.client.properties[4] = self.client.properties[4].split(" = ")
                                self.client.properties[4][1] = self.client.properties[4][1].split(", ")
                                self.client.properties[4][1].remove("\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]))
                                self.client.properties[4][1] = ", ".join(self.client.properties[4][1])
                                self.client.properties[4] = " = ".join(self.client.properties[4])
                                self.f = open(self.client.data_file,"w")
                                self.f.write("\n".join(self.client.properties))
                                self.f.close()
                                self.client.send("REMOVE\\friend\\OK")
                            else :
                                self.client.send("REMOVE\\friend\\404")
                        else:
                            self.client.send("REMOVE\\friend\\REFUSED")
                            log("Le client "+str(self.client.infos)+" a tente de supprimer l'un de ses ami alors qu'il n'etait pas connecte. Son acces a ete refuse. Il va etre deconnecte.")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "BACKUP" and len(self.msg_recu.split("\\")) > 1:
                    if self.client.logged_in:
                        """self.f = open("clients/Backups/"+self.client.username+"/backup.zip","w")
                        self.f.write("\\".join(self.msg_recu.split("\\")[1:]))
                        self.f.close()"""
                        verif_path("clients/Backups/"+self.client.username+"/backup.zip")
                        self.bkp_file = open("clients/Backups/"+self.client.username+"/backup.zip", 'wb')
                        self.bkp = binascii.unhexlify("\\".join(self.msg_recu.split("\\")[1:]))
                        self.bkp_file.write(self.bkp)
                        self.bkp_file.close()
                    else:
                        self.client.send("BACKUP\\REFUSED")
                        self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "START" and len(self.msg_recu.split("\\")) > 1:
                    if self.msg_recu.split("\\")[1] == "s_conv" and len(self.msg_recu.split("\\")) > 3:
                        if self.client.logged_in:
                            try:
                                os.mkdir("clients/Keys/"+self.msg_recu.split("\\")[2])
                            except:
                                pass
                            verif_path("clients/Backups/"+self.client.username+"/backup.zip")
                            self.f = open("clients/Keys"+"/"+self.msg_recu.split("\\")[2]+"/"+self.client.username+"key","w")
                            self.f.write("\\".join(self.msg_recu.split("\\")[3:]))
                            self.f.close()
                            self.client.send("S_CONV\\CREATED")
                            log("Une conversation entre "+self.client.username+" et "+self.msg_recu.split("\\")[2]+" a ete cree avec succes.")
                        else:
                            log("Le client "+self.client.infos+" a tente de demarrer une nouvelle conversation avec "+self.msg_recu.split("\\")[2]+" sans etre connecte. Il va etre deconnecte.")
                            self.client.send("S_CONV\\REFUSED")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)
                    elif self.msg_recu.split("\\")[1] == "group" and len(self.msg_recu.split("\\")) > 6 :
                        if self.client.logged_in:
                            self.nom = self.msg_recu.split("\\")[2]
                            self.key = self.msg_recu.split("\\")[3]
                            self.lenth = self.msg_recu.split("\\")[4]
                            self.dests = self.msg_recu.split("\\")[5:]
                            for self.x in self.dests:
                                verif_path("clients/groups/"+self.x+"/"+self.nom+".info")
                                self.fileinfo = open("clients/groups/"+self.x+"/"+self.nom+".info", "w")
                                self.fileinfo.write("Key="+self.key+"\nMembers="+", ".join(self.dests))
                                self.fileinfo.close()
                            self.client.send("GROUP\\CREATED")
                        else:
                            log("Le client "+self.client.infos+" a tente de demarrer un nouveau groupe avec "+self.msg_recu.split("\\")[5:]+" sans etre enregistre. Il va etre deconnecte.")
                            self.client.send("GROUP\\REFUSED")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)


                else:
                    self.client.send("ACCES DENIED")
                    log("Le client "+str(self.client.infos)+" a envoye un message non repertorie. Son acces a ete refuse. Il va etre deconnecte.")
                    self.client.disconnect("Action non autorisee > "+self.msg_recu)
                self.msg_recu=""
            except:
                print "Une erreur est survenue dans le thread "+str(threading.currentThread())
                filename = ""
                for x in range(10):
                    filename += str(random.randint(0, 9))
                print "Les informations sur le thread courant sont enregistrées dans le fichier errors/"+filename
                verif_path("errors/"+filename)
                self.f = open("errors/"+filename, "w")
                self.f.write("******************** RAPPORT D'ERREUR ********************\n\n\n\n")
                self.f.write("----- GLOBAL INFOS -----\n\nDate : "+", ".join(datetime.datetime.isoformat(datetime.datetime.now()).split("T"))+"\nPlateforme : "+sys.platform+"\nVersion du serveur : "+version+"\n"+"\n\n")
                self.f.write("----- SPECIFIC INFOS -----\n\nInformations generales sur le client : "+str(self.client.infos)+"\nConnecte en tant que : "+self.client.username+"\nFichier de configuration du client : "+self.client.data_file+"\nMessages envoyes par le client : "+str(self.msgs_rcved)+"\nDerniere requete : "+self.msg_recu+"\nDetails de l'erreur : "+str(sys.exc_info())+"\n")
                self.f.close()
                log("Une erreur est survenue. Details enregistres dans errors/"+filename)
        print "Boucle finie dans le thread "+str(threading.currentThread())



print "Demarrage du serveur.                                         "
accepter_client = Accepter_client()
accepter_client.start()
clients = []
infos_clients = {}
serveur_lance = True
msg_recu = ""
