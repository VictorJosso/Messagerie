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
import pickle

import addUser
import Crypt as crpt
import emailSender

version  = "1.0"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Serveur pour la messagerie, par Victor Josso")
    parser.add_argument("-p", "--port", help="Définissez le port sur lequel écouter (default : "+str(port)+")")

    return parser.parse_args()

def log(text):
    log = open("log.txt", "a")
    log.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"]"+text+"\n")
    log.close()

def verif_path(path, folder = False):
    if folder:
        path+=os.sep+"creating_file"
    if not os.path.exists(path):
        original_path = os.getcwd()
        path_to_create = ""
        for x in path.split(os.sep)[:len(path.split(os.sep))-1]:
            path_to_create += x+os.sep
            try:
                os.mkdir(path_to_create)
            except Exception as error:
                pass
        if not folder:
            a = open(path, "w")
            a.close()

    else:
        pass

def find_key_in_dict(dict, phrase):
	for cle, val in dict.items():
		if val == phrase:
			return cle
	return None


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
        self.groupsids = {}
        self.private_key = ""

    def get_groupsids(self):
        verif_path(os.sep.join(self.data_file.split("/"))+"-datas"+os.sep+"groups_allowed.pkl")
        self.groupsids_f = open(self.data_file+"-datas/groups_allowed.pkl", "r")
        try:
            self.groupsids = pickle.Unpickler(self.groupsids_f).load()
        except:
            self.groupsids = {}
        self.groupsids_f.close()

    def update_groupsids(self):
        self.groupsids_f = open(self.data_file+"-datas/groups_allowed.pkl", "w")
        self.pklgroupsids = pickle.Pickler(self.groupsids_f)
        self.pklgroupsids.dump(self.groupsids)
        self.groupsids_f.close()

    def send(self,message):
        """
        Envoie un message au client.
        """
        self.connection.send((message+chr(23)).encode("utf-8"))
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
    def get_groups_allowed(self):
        verif_path("clients/groups/members/"+self.username+"/members.pkl")
        self.members_file = open("clients/groups/members/"+self.username+"/members.pkl", "r")
        try:
            self.unpickler = pickle.Unpickler(self.members_file)
            self.members = self.unpickler.load()
        except:
            self.members = {}
        self.members_file.close()
        return self.members

    def get_private_key(self):
        verif_path(self.data_file+"-datas"+os.sep+"RSAPrivateKey.key")
        self.file = open(self.data_file+"-datas"+os.sep+"RSAPrivateKey.key", "r")
        self.private_key = self.file.read()
        self.file.close()


    def set_groups_allowed(self, members):
        self.members_file = open("clients/groups/members/"+self.username+"/members.pkl", "w")
        self.pickler = pickle.Pickler(self.members_file)
        self.pickler.dump(members)
        self.members_file.close()


hote = ""
port = 26281

args = parse_arguments()

class Public_Keys:
    def __init__(self):
        self.update_keys()

    def update_keys(self):
        verif_path("clients"+os.sep+"convert-tables"+os.sep+"username_to_publicKey")
        self.file = open("clients"+os.sep+"convert-tables"+os.sep+"username_to_publicKey", "r")
        self.U = pickle.Unpickler(self.file)
        try:
            self.keys = self.U.load()
        except:
            self.keys = {}
        self.file.close()

    def get_key(self, username):
        for self.x in self.keys.keys():
            if self.x == username:
                return self.keys[self.x]
        return None




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
        self.next_msg = str()

    def run(self):
        self.msgs_rcved = []
        self.msg_recu = str()
        while not self.has_to_stop:
            try:
                try:
                    while self.msg_recu == '' or not chr(23) in self.msg_recu.strip():
                        self.msg_recu += self.client.recv(33554432).decode("utf-8")
                    self.next_msg = self.msg_recu[self.msg_recu.index(chr(23))+1:]
                    self.msg_recu = self.msg_recu[:self.msg_recu.index(chr(23))].strip()
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
                        self.f = open("clients/datas/"+"/".join(self.msg_recu.split("\\")[2:]),"r")
                        self.infos_client = self.f.read()
                        self.email_verified = self.infos_client.split("\n")[2].split(" = ")[1]
                        self.f.close()
                        if not self.email_verified == "True":
                            self.client.send("CONNECT\\CONFIRM_EMAIL")
                            raise ValueError
                        if " = ".join(self.infos_client.split("\n")[0].split(" = ")[1:]) == self.msg_recu.split("\\")[1]:
                            self.client.send("CONNECT\\OK")
                        else:
                            raise IOError
                        self.client.id_client = self.infos_client.split("\n")[3].split(" = ")[1]
                        self.client.username = self.infos_client.split("\n")[0].split(" = ")[1]
                        self.client.friends = [x for x in self.infos_client.split("\n")[4].split(" = ")[1].split(", ") if not x == " "]
                        self.client.logged_in = True
                        self.client.properties = self.infos_client.split("\n")
                        self.client.data_file = "clients/datas/"+"/".join(self.msg_recu.split("\\")[2:])
                        threading.currentThread().setName(self.client.username)
                        log("Client "+str(self.client.infos)+" connecte en tant que "+str(self.client.username)+" id "+str(self.client.id_client))
                    except IOError:
                        self.client.send("CONNECT\\FAILED")
                    except ValueError:
                        pass
                elif self.msg_recu.split("\\")[0] == "VERIF_MAIL" and len(self.msg_recu.split("\\")) == 3:
                    try:
                        print 'Trying to open file : '+"clients/datas/"+self.msg_recu.split("\\")[1]
                        self.file = open("clients/datas/"+self.msg_recu.split("\\")[1], "r")
                        print "Done."
                        self.infos = self.file.read()
                        self.file.close()
                        if self.infos.split("\n")[2].split(" = ")[1] == "False":
                            if self.infos.split("\n")[7].split(" = ")[1] == self.msg_recu.split("\\")[2]:
                                self.file = open("clients/datas/"+self.msg_recu.split("\\")[1], "w")
                                self.to_write = []
                                for self.x in self.infos.split("\n"):
                                    if not self.x.split(" = ")[0] == "email_verified":
                                        self.to_write.append(self.x)
                                    else:
                                        self.to_write.append("email_verified = True")
                                self.file.write("\n".join(self.to_write))
                                self.file.close()
                                self.client.send("VERIF_MAIL\\VERIFIED")
                            else:
                                self.client.send("VERIF_MAIL\\INVALID")
                        else:
                            self.client.send("VERIF_MAIL\\ALREADY_DONE")
                    except:
                        self.client.send("VERIF_MAIL\\UNABLE")
                elif self.msg_recu.split("\\")[0]=="REGISTER" and len(self.msg_recu.split("\\")) >= 6:
                    addUser.createPath()
                    verif_path("clients"+os.sep+"convert-tables"+os.sep+"users")
                    verif_path("clients"+os.sep+"convert-tables"+os.sep+"mails")
                    self.users = open(str("clients"+os.sep+"convert-tables"+os.sep+"users"),'r').read().split("\n")
                    self.mails = open("clients"+os.sep+"convert-tables"+os.sep+"mails",'r').read().split("\n")
                    if not self.msg_recu.split("\\")[1] in self.users:
                        if not self.msg_recu.split("\\")[3] in self.mails:
                            try:
                                self.verif_code = random.randint(100000, 999999)
                                addUser.createUser(self.msg_recu.split("\\")[1], self.msg_recu.split('\\')[3], self.msg_recu.split('\\')[2], self.client.infos[0], self.msg_recu.split("\\")[4], "\\".join(self.msg_recu.split("\\")[5:]), self.verif_code)
                                public_Keys.update_keys()
                                emailSender.envoyer_confirmation(self.msg_recu.split('\\')[3], self.verif_code, self.msg_recu.split("\\")[1])
                                self.client.send("REGISTER\\OK")
                            except:
                                self.client.send("REGISTER\\ERROR")
                                print "Une erreur est survenue dans le thread "+str(threading.currentThread())
                                filename = ""
                                for x in range(10):
                                    filename += str(random.randint(0, 9))
                                print "Les informations sur le thread courant sont enregistrees dans le fichier errors/"+filename
                                verif_path("errors"+os.sep+filename)
                                self.f = open("errors"+os.sep+filename, "w")
                                self.f.write("******************** RAPPORT D'ERREUR ********************\n\n\n\n")
                                self.f.write("----- GLOBAL INFOS -----\n\nDate : "+", ".join(datetime.datetime.isoformat(datetime.datetime.now()).split("T"))+"\nPlateforme : "+sys.platform+"\nVersion du serveur : "+version+"\n"+"\n\n")
                                self.f.write("----- SPECIFIC INFOS -----\n\nInformations generales sur le client : "+str(self.client.infos)+"\nConnecte en tant que : "+str(self.client.username)+"\nFichier de configuration du client : "+str(self.client.data_file)+"\nMessages envoyes par le client : "+str(self.msgs_rcved)+"\nDerniere requete : "+str(self.msg_recu)+"\nDetails de l'erreur : "+str(sys.exc_info())+"\n")
                                self.f.close()
                                log("Une erreur est survenue. Details enregistres dans errors/"+filename)
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
                            if len(self.msg_recu.split("\\"))==3:
                                if self.msg_recu.split("\\")[2] == "s_conv":
                                    self.files = os.listdir("clients"+os.sep+"messages"+os.sep+self.client.username)
                                    """print self.dir_contains
                                    self.files = []
                                    for x in self.dir_contains:
                                        if os.path.isfile(x):
                                            self.files.append(x)"""
                                    self.client.send("GIVE\\unreaded\\s_conv\\"+str(len(self.files)))
                                elif self.msg_recu.split("\\")[2] == "group":
                                    verif_path("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"new_groups"+os.sep+self.client.username, folder = True)
                                    verif_path("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined"+os.sep+self.client.username, folder = True)
                                    self.files = os.listdir("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"new_groups"+os.sep+self.client.username)
                                    self.old_groups = os.listdir("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined"+os.sep+self.client.username)
                                    self.client.send("GIVE\\unreaded\\groups\\"+str(len(self.files)+len(self.old_groups)))
                            elif len(self.msg_recu.split("\\"))==4:
                                if self.msg_recu.split("\\")[2] == "s_conv":
                                    self.conv_name = self.files[int(self.msg_recu.split("\\")[3])]
                                    if os.path.exists("clients/Keys/"+self.client.username+"/"+self.conv_name+"key"):
                                        verif_path("clients/Keys/"+self.client.username+"/"+self.conv_name+"key")
                                        self.key = open("clients/Keys/"+self.client.username+"/"+self.conv_name+"key","r")
                                        self.client.send("KEY\\"+self.conv_name+"\\"+self.key.read())
                                        self.key.close()
                                        os.remove("clients/Keys/"+self.client.username+"/"+self.conv_name+"key")
                                        #time.sleep(1)
                                    verif_path("clients/messages/"+self.client.username+"/"+self.conv_name)
                                    self.conv = open("clients/messages/"+self.client.username+"/"+self.conv_name, "r").read()
                                    self.client.send("GIVE\\unreaded\\s_conv\\"+self.conv_name+"\\"+self.conv)
                                    os.remove("clients/messages/"+self.client.username+"/"+self.conv_name)
                                elif self.msg_recu.split("\\")[2] == "group":
                                    if int(self.msg_recu.split("\\")[3]) < len(self.files):
                                        self.conv_name = self.files[int(self.msg_recu.split("\\")[3])]
                                        if os.path.exists("clients/groups/infos/"+self.client.username+"/"+self.conv_name+".info"):
                                            self.config = open("clients/groups/infos/"+self.client.username+"/"+self.conv_name+".info", "r")
                                            self.a_envoyer = "INFOS\\"+self.conv_name+"\\"+"\\".join(self.config.read().split("\n"))
                                            self.client.send(self.a_envoyer)
                                            self.config.close()
                                            os.remove("clients/groups/infos/"+self.client.username+"/"+self.conv_name+".info")
                                            self.client.get_groupsids()
                                            self.client.groupsids[self.a_envoyer.split("\\")[4].split("=")[1]] = self.a_envoyer.split("\\")[1]
                                            self.client.update_groupsids()
                                        self.client.get_groupsids()
                                        self.group_id = find_key_in_dict(self.client.groupsids, self.a_envoyer.split("\\")[1])
                                        self.conv = open("clients/groups/messages/new_groups/"+self.client.username+"/"+self.conv_name, "r")
                                        self.client.send("GIVE\\unreaded\\groups\\"+self.group_id+"\\"+self.conv.read())
                                        self.conv.close()
                                        os.remove("clients/groups/messages/new_groups/"+self.client.username+"/"+self.conv_name)
                                    elif int(self.msg_recu.split("\\")[3]) >= len(self.files) and int(self.msg_recu.split("\\")[3])-len(self.files) < len(self.old_groups):
                                        self.client.get_groupsids()
                                        self.conv_name = self.old_groups[int(self.msg_recu.split("\\")[3])-len(self.files)]
                                        if self.conv_name in self.client.groupsids.keys():
                                            self.conv_file = open("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined"+os.sep+self.client.username+os.sep+self.conv_name, "r")
                                            self.client.send("GIVE\\unreaded\\groups\\"+self.conv_name+"\\"+self.conv_file.read())
                                            self.conv_file.close()
                                            os.remove("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined"+os.sep+self.client.username+os.sep+self.conv_name)
                                    else:
                                        self.client.send("GIVE\\ERROR")
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
                    elif self.msg_recu.split("\\")[1] == "private_key":
                        if self.client.logged_in:
                            self.client.get_private_key()
                            self.client.send("GIVE\\PRIVATE\\"+self.client.private_key)
                        else:
                            self.client.send("GIVE\\REFUSED")
                    elif self.msg_recu.split("\\")[1] == "publickey" and len(self.msg_recu.split('\\')) == 3:
                        if self.client.logged_in:
                            if public_Keys.get_key(self.msg_recu.split("\\")[2]):
                                self.client.send("GIVE\\PUBLIC\\"+self.msg_recu.split('\\')[1]+"\\"+public_Keys.get_key(self.msg_recu.split("\\")[2]))
                            else:
                                self.client.send("GIVE\\PUBLIC\\UNABLE")
                        else:
                            self.client.send("GIVE\\PUBLIC\\REFUSED")
                elif self.msg_recu.split("\\")[0] == "SEND" and len(self.msg_recu.split("\\")) > 2:
                    if self.client.logged_in:
                        verif_path("clients/messages/"+self.msg_recu.split("\\")[1]+"/"+self.client.username)
                        self.f = open("clients/messages/"+self.msg_recu.split("\\")[1]+"/"+self.client.username,"a")
                        self.f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+self.client.username+"]"+"]".join("\\".join(self.msg_recu.split("\\")[2:]).split("]")[1:])+"\n")
                        self.f.close()
                        self.client.send("SEND\\OK")
                    else :
                        self.client.send("SEND\\REFUSED")
                        log("Le client "+str(self.client.infos)+" a tente d'envoyer un message a "+self.msg_recu.split("\\")[1]+" alors qu'il n'etait pas connecte. Son acces a ete refuse. Il va etre deconnecte.")
                        self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "SEND_GROUP"  and len(self.msg_recu.split("\\")) >= 4:
                    if self.client.logged_in:
                        self.destinataires = self.msg_recu.split("\\")[1].split(", ")
                        self.id = self.msg_recu.split("\\")[2]
                        self.msg = "\\".join(self.msg_recu.split("\\")[3:])
                        self.client.get_groupsids()
                        if self.id in self.client.groupsids.keys():
                            for self.x in self.destinataires:
                                verif_path("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined"+os.sep+self.x, folder = True)
                                self.file = open("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"groups_already_joined"+os.sep+self.x+os.sep+self.id, "a")
                                self.file.write(self.msg+"\n")
                                self.file.close()
                            self.client.send("SEND\\OK")
                        else:
                            self.client.send("SEND\\REFUSED")
                    else:
                        self.client.send("SEND\\REFUSED")
                elif self.msg_recu.split("\\")[0] == "ADD" and len(self.msg_recu.split("\\")) > 1:
                    if self.msg_recu.split("\\")[1] == "friend" and len(self.msg_recu.split("\\")) > 2:
                        if self.client.logged_in:
                            verif_path("clients/convert-tables/users")
                            self.users = open("clients/convert-tables/users",'r').read().split("\n")
                            if not "\\".join(self.msg_recu.split("\\")[2:len(self.msg_recu.split("\\"))]) == self.client.username:
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
                                self.client.send("ADD\\FRIEND\\REFUSED\\ADDING_OWN_USERNAME")
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
                
                elif self.msg_recu.split("\\")[0] == "SET":
                    if self.msg_recu.split("\\")[1] == "PROFILE_PICTURE" and len(self.msg_recu.split("\\")) == 3 :
                        if self.client.logged_in:
                            self.picture_file = open(self.client.data_file+"-datas"+os.sep+"PROFILE_PICTURE.png", "wb")
                            self.picture_file.write(binascii.unhexlify(self.msg_recu.split("\\")[2]))
                            self.picture_file.close()

                            self.client.send("SET\\PROFILE_PICTURE\\OK")
                        else:
                            self.client.send("SET\\PROFILE_PICTURE\\REFUSED")

                elif self.msg_recu.split("\\")[0] == "BACKUP" and len(self.msg_recu.split("\\")) > 1:
                    if self.client.logged_in:
                        """self.f = open("clients/Backups/"+self.client.username+"/backup.zip","w")
                        self.f.write("\\".join(self.msg_recu.split("\\")[1:]))
                        self.f.close()"""
                        verif_path("clients"+os.sep+"Backups"+os.sep+self.client.username+os.sep+"backup.zip")
                        self.bkp_file = open("clients"+os.sep+"Backups"+os.sep+self.client.username+os.sep+"backup.zip", 'wb')
                        self.bkp = binascii.unhexlify("\\".join(self.msg_recu.split("\\")[1:]))
                        self.bkp_file.write(self.bkp)
                        self.bkp_file.close()
                        self.client.send("BACKUP\\OK")

                    else:
                        self.client.send("BACKUP\\REFUSED")
                        self.client.disconnect("Action non autorisee > "+self.msg_recu)
                elif self.msg_recu.split("\\")[0] == "START" and len(self.msg_recu.split("\\")) > 1:
                    if self.msg_recu.split("\\")[1] == "s_conv" and len(self.msg_recu.split("\\")) > 3:
                        if self.client.logged_in:
                            try:
                                os.mkdir("clients"+os.sep+"Keys"+os.sep+self.msg_recu.split("\\")[2])
                            except:
                                pass
                            verif_path("clients"+os.sep+"Backups"+os.sep+self.client.username+os.sep+"backup.zip")
                            self.f = open("clients"+os.sep+"Keys"+os.sep+self.msg_recu.split("\\")[2]+os.sep+self.client.username+"key","w")
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
                            self.new_id = ""
                            verif_path("clients"+os.sep+"convert-tables"+os.sep+"groupsids")
                            self.groupsids_file = open("clients"+os.sep+"convert-tables"+os.sep+"groupsids", "r")
                            self.groupsids = self.groupsids_file.read()
                            self.groupsids_file.close()
                            self.groupsids = self.groupsids.split("\n")
                            while True:
                                for self.x in range(12):
                                    self.new_id += str(random.randint(0, 9))
                                if not self.new_id in self.groupsids:
                                    break
                                else:
                                    self.new_id = ""
                            self.groupsids_file = open("clients"+os.sep+"convert-tables"+os.sep+"groupsids", "a")
                            self.groupsids_file.write(self.new_id+"\n")
                            self.groupsids_file.close()

                            for self.x in self.dests:
                                verif_path("clients"+os.sep+"groups"+os.sep+"infos"+os.sep+""+self.x+os.sep+self.nom+".info")
                                verif_path("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"new_groups"+os.sep+self.x+os.sep+self.nom)
                                self.fileinfo = open("clients"+os.sep+"groups"+os.sep+"infos"+os.sep+self.x+os.sep+self.nom+".info", "w")
                                self.messagefile = open("clients"+os.sep+"groups"+os.sep+"messages"+os.sep+"new_groups"+os.sep+self.x+os.sep+self.nom, "w")
                                self.fileinfo.write("Key="+self.key+"\nMembers="+", ".join(self.dests)+"\nGroup id="+self.new_id+"\nName="+self.nom)
                                self.messagefile.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\SERVER"+"]"+crpt.crypt_message(self.client.username+" has created this group with "+", ".join(self.dests), self.key))
                                self.fileinfo.close()
                                self.messagefile.close()
                            self.client.send("GROUP\\CREATED\\"+self.new_id)
                        else:
                            log("Le client "+self.client.infos+" a tente de demarrer un nouveau groupe avec "+self.msg_recu.split("\\")[5:]+" sans etre enregistre. Il va etre deconnecte.")
                            self.client.send("GROUP\\REFUSED")
                            self.client.disconnect("Action non autorisee > "+self.msg_recu)


                else:
                    self.client.send("ACCES DENIED")
                    log("Le client "+str(self.client.infos)+" a envoye un message non repertorie. Son acces a ete refuse. Il va etre deconnecte.")
                    self.client.disconnect("Action non autorisee > "+self.msg_recu)
                self.msg_recu=""

            except Exception as self.e:
                print "Une erreur est survenue dans le thread "+str(threading.currentThread())
                self.filename = ""
                for x in range(10):
                    self.filename += str(random.randint(0, 9))
                print "Les informations sur le thread courant sont enregistrees dans le fichier errors/"+self.filename
                verif_path("errors"+os.sep+self.filename)
                self.f = open("errors/"+self.filename, "w")
                self.f.write("******************** RAPPORT D'ERREUR ********************\n\n\n\n")
                self.f.write(unicode("----- GLOBAL INFOS -----\n\nDate : "+", ".join(datetime.datetime.isoformat(datetime.datetime.now()).split("T"))+"\nPlateforme : "+sys.platform+"\nVersion du serveur : "+version+"\n"+"\n\n"))
                self.squelette = "----- SPECIFIC INFOS -----\n\nInformations generales sur le client : \nConnecte en tant que : \nFichier de configuration du client : \nMessages envoyes par le client : \nDerniere requete : \nDetails de l'erreur : ,"
                """print str(self.client.infos)
                print str(self.client.username)
                print str(self.client.data_file)
                print str(self.msgs_rcved)
                print str(self.msg_recu)
                print str(sys.exc_info())
                print str(self.e)
                print self.squelette"""
                self.f.write("----- SPECIFIC INFOS -----\n\nInformations generales sur le client : "+str(self.client.infos)+"\nConnecte en tant que : "+str(self.client.username)+"\nFichier de configuration du client : "+str(self.client.data_file)+"\nMessages envoyes par le client : "+str(self.msgs_rcved)+"\nDerniere requete : "+str(self.msg_recu)+"\nDetails de l'erreur : "+str(sys.exc_info())+", "+unicode(self.e)+"\n")
                self.f.close()
                self.client.send("ERROR\\"+self.filename)
                log("Une erreur est survenue. Details enregistres dans errors/"+self.filename)
        print "Boucle finie dans le thread "+str(threading.currentThread())



print "Demarrage du serveur.                                       "
public_Keys = Public_Keys()
accepter_client = Accepter_client()
accepter_client.start()
clients = []
infos_clients = {}
serveur_lance = True
msg_recu = ""
