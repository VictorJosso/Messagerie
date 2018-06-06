# -*- coding: utf-8 -*-

"""Code par Victor Josso"""

#from __future__ import unicode_literals
import socket
import getpass
import hashlib
import threading
import sys
import datetime
import time
import os
import pickle
import zipfile
import glob
import shutil
import binascii
import argparse
from Crypto.PublicKey import RSA

import Crypt as crpt
import Uncrypt as ucrpt
import generate_random_passwords as r_pass

hote = "josso.fr"
port = 26281

if  not sys.platform[:3] == "win":
	colours = {
		"default"    :    "\033[0m",
		# style
		"bold"       :    "\033[1m",
		"underline"  :    "\033[4m",
		"blink"      :    "\033[5m",
		"reverse"    :    "\033[7m",
		"concealed"  :    "\033[8m",
		# couleur texte
		"black"      :    "\033[30m",
		"red"        :    "\033[31m",
		"green"      :    "\033[32m",
		"yellow"     :    "\033[33m",
		"blue"       :    "\033[34m",
		"magenta"    :    "\033[35m",
		"cyan"       :    "\033[36m",
		"white"      :    "\033[37m",
		# couleur fond
		"on_black"   :    "\033[40m",
		"on_red"     :    "\033[41m",
		"on_green"   :    "\033[42m",
		"on_yellow"  :    "\033[43m",
		"on_blue"    :    "\033[44m",
		"on_magenta" :    "\033[45m",
		"on_cyan"    :    "\033[46m",
		"on_white"   :    "\033[47m" }
else:
	colours = {
		"default"    :    "",
		# style
		"bold"       :    "",
		"underline"  :    "",
		"blink"      :    "",
		"reverse"    :    "",
		"concealed"  :    "",
		# couleur texte
		"black"      :    "",
		"red"        :    "",
		"green"      :    "",
		"yellow"     :    "",
		"blue"       :    "",
		"magenta"    :    "",
		"cyan"       :    "",
		"white"      :    "",
		# couleur fond
		"on_black"   :    "",
		"on_red"     :    "",
		"on_green"   :    "",
		"on_yellow"  :    "",
		"on_blue"    :    "",
		"on_magenta" :    "",
		"on_cyan"    :    "",
		"on_white"   :    "" }

def log(text):
	f = open(username+"log", "a")
	f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"]"+text+"\n")
	f.close()

def verif_path(path, folder = False):
	if folder:
		path+=os.sep+"creating_file"
	if not os.path.exists(path):
		original_path = os.getcwd()
		for x in path.split(os.sep)[:len(path.split(os.sep))-1]:
			try:
				os.mkdir(x)
			except Exception as error:
				pass
			os.chdir(x)
		os.chdir(original_path)
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

def parse_arguments():
	parser = argparse.ArgumentParser(description="Client pour la messagerie, par Victor Josso")
	parser.add_argument("--hote", help="Définissez l'hote auquel se connecter (default : "+str(hote)+")")
	parser.add_argument("-p", "--port", help="Définissez le port auquel se connecter (default : "+str(port)+")")

	return parser.parse_args()

class Releve(threading.Thread):
	def __init__(self):
		self.msg_received = False
		threading.Thread.__init__(self)
		self.running = True
		self.isanerror = False
		self.i = 0
		self.msg = str()
	def run(self):
		while self.running:
			pass

	def releve(self):
		self.msg = str()
		while self.msg == '' or not self.msg.strip()[len(self.msg.strip())-1] == chr(23):
			try:
				self.msg += connection_server.recv(33554432)
			except Exception as e:
				print "Le serveur est injoignable. Veuillez verifier votre connexion internet et reessayer. Si votre connexion est stable, et que le probleme persiste, il est probable que le serveur soit hors ligne et nous vous suggerons de patienter jusqu'a ce qu'il soit remis en service. Merci."
				self.isanerror = True
				return "ERROR"
			self.i +=1
		self.msg = self.msg.strip()
		self.msg = self.msg[:len(self.msg)-1]
		self.i = 0
		log(self.msg) #reception du message envoye par le server.


		if self.msg == "SERVER\\SHUTDOWN":
			#Permet de deverouiller le server et d'afficher un message pour l'utilisateur en cas d'arret programme du server.
			connection_server.send("OK"+chr(23))
			self.running = False
			print "Server has been shutdowned. Please wait until it restarts."
			server_reachable = False
			return 0
		elif self.msg.split("\\")[0] == "ERROR":
			if sys.platform[:3] == "win":
				error_f = open("alert_error.vbs", "w")
				error_f.write("MsgBox \""+"An error occured in your server thread. Restart the application. This is not due to you and you can't do anything except contact support and give them this error code : "+msg.split("\\")[1]+"\", 16, \"Erreur serveur\"")
				error_f.close()
				os.system("alert_error.vbs")
				self.running = False
				server_reachable = False
				return 0

		else:
			#Enregistement du message dans un fichier afin de le recuperer dans le MainThread.
			while True:
				try:
					with verrou:
						f = open("response", "w")
						f.write(self.msg)
						f.close()
					self.msg_received = True
					return True
					break
				except:
					print "Erreur dans la recuperation de la reponse.\r",
		if not self.running:
			return 0

def zipdirectory(filezip, pathzip):
	#Cette fonction cree une archive Zip. Elle est utlisee pour faire des sauvegardes lors de la deconnexion.
	lenpathparent = len(pathzip)+1   ## utile si on veut stocker les chemins relatifs
	def _zipdirectory(zfile, path):
		for i in glob.glob(path+'/*'):
			if os.path.isdir(i): _zipdirectory(zfile, i )
			else:
				zfile.write(i, i[lenpathparent:]) ## zfile.write(i) pour stocker les chemins complets
	zfile = zipfile.ZipFile(filezip,'w',compression=zipfile.ZIP_DEFLATED)
	_zipdirectory(zfile, pathzip)
	zfile.close()

def backup():
	global username
	global mdp
	zipdirectory("backup.zip", username)
	backup_crpt = crpt.crypt("backup.zip", mdp)
	bkp_file = open(backup_crpt, 'rb')
	msg_to_send = "BACKUP\\"+binascii.hexlify(bkp_file.read())
	bkp_file.close()
	print "Envoi de la sauvegarde..."
	connection_server.send(msg_to_send+chr(23))
	msg_from_server = attendre_reponse()
	if msg_from_server == "BACKUP\\OK":
		print "Envoye ! "
		os.remove(backup_crpt)
		with open("bkp_sended.txt", "a") as f:
			f.write(msg_to_send)
		return backup_crpt
	else:
		print "Une erreur est survenue lors de l'envoi de la sauvegarde. Vous n'allez pas être deconnecte."
		return "ERROR"

def dezip(filezip, pathdst = ''):
	if pathdst == '': pathdst = os.getcwd()  ## on dezippe dans le repertoire locale
	zfile = zipfile.ZipFile(filezip, 'r')
	for i in zfile.namelist():  ## On parcourt l'ensemble des fichiers de l'archive
		if os.path.isdir(i):   ## S'il s'agit d'un repertoire, on se contente de creer le dossier
			try: os.makedirs(pathdst + os.sep + i)
			except: pass
		else:
			try: os.makedirs(pathdst + os.sep + os.path.dirname(i))
			except: pass
			data = zfile.read(i)                   ## lecture du fichier compresse
			fp = open(pathdst + os.sep + i, "wb")  ## creation en local du nouveau fichier
			fp.write(data)                         ## ajout des donnees du fichier compresse dans le fichier local
			fp.close()
	zfile.close()

def get_backup():
	global username
	global mdp
	global private_key

	connection_server.send("GET\\backup"+chr(23))
	msg_from_server = attendre_reponse()
	if msg_from_server.split("\\")[:3] == ["GIVE", "backup", "OK"]:
		bkp = msg_from_server.split("\\")[3]
		bkp = binascii.unhexlify(bkp)
		new_backup = open("backup.zip","wb")
		new_backup.write(bkp)
		new_backup.close()
		ucrpt.uncrypt("backup.zip", mdp)
		dezip("backup.zip", username)
		os.remove("backup.zip")
	elif msg_from_server.split("\\")[:3] == ["GIVE", "backup", "UNABLE"]:
		print "Recuperation de vos cles."
		connection_server.send("GET\\private_key"+chr(23))
		msg_from_server = attendre_reponse()
		private_key = ucrpt.uncrypt_message("\\".join(msg_from_server.split("\\")[2:]), mdp)
		try:
			os.mkdir(username)
		except:
			pass
		f = open(username+os.sep+"RSAPrivateKey.key", "w")
		f.write(private_key)
		private_key = RSA.importKey(private_key)
		f.close()
	elif msg_from_server.split("\\") == "GET\\REFUSED":
		print "Accès refusé. Veuillez réessayer !"
		os.remove("log_infos.pkl")
		sys.exit()

def verif_answer(prompt, rep_available, error_message):
	print prompt
	rep = raw_input(">>")
	while not rep in rep_available:
		print error_message
		print prompt
		rep = raw_input(">>")
	return rep

def attendre_reponse():
	while not (releve.msg_received or releve.isanerror) :
		releve.releve()
	if releve.msg_received:
		releve.msg_received = False
		msg_from_server = open("response", "r").read()
		while 1:
			try:
				os.remove("response")
				break
			except :
				pass
		if msg_from_server == "SERVER\\SHUTDOWN":
			sys.exit()
		else:

			return msg_from_server
	else:
		sys.exit()

def log_in(already_in = False, user = "", passwd = "", hash_512 = ""):
	global username
	global mdp
	if not already_in :
		print "                                           \r", #Permet d'effacer le message "Connexion au server en cours..."
		if not os.path.exists("log_infos.pkl"): #Aucune info de log n'est enregistree.
			ans = verif_answer("Bienvenue sur [NOM]\nVous pouvez effectuer les actions suivantes : \n\n\t[1]Vous connecter\n\t[2]Vous inscrire\n\t[99]Quitter l'application",["1","2", "99"],"Veuillez sasir l'une des valeurs entre crochets.")
			if ans == "1":
				while True:
					username = raw_input("Nom d'utilisateur : ")
					while not username :
						print "Le nom d'utilisateur ne doit pas etre vide... Veuillez réessayer !"
						username = raw_input("Nom d'utilisateur : ")
					passwd = getpass.getpass("Mot de passe : ")
					while not passwd :
						print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
						passwd = getpass.getpass("Mot de passe : ")


					infos = hashlib.sha512((username+" : "+passwd).encode("utf-8")).hexdigest() #Chiffrage de la combinaison username+" : "+pwd grace au SHA512.
					connection_server.send(("CONNECT\\"+username+"\\"+infos+chr(23))) #Envoi des infos de connexion.
					msg_from_server = attendre_reponse()
					if msg_from_server.split("\\")[0] == 'CONNECT' and msg_from_server.split("\\")[1] == "OK":
						print colours["green"]+colours["reverse"]+colours["bold"]+'Identification réussie !'+colours["default"] #Le serveur a repondu positivement.
						f = open("log_infos.pkl", "w")
						P = pickle.Pickler(f)
						log_infos = {"user":username, "passwd":passwd, "hash":infos}
						P.dump(log_infos) #Sauvegarde des infos de log dans un fichier. Ce fichier sera supprime si l'utilisateur demande sa deconnexion.
						f.close()
						mdp = passwd
						get_backup() #Recuperation de la sauvegarde.
						verif_path(username+os.sep+"messages", True)
						break
					else :
						#Le serveur a refuse l'authentification.
						print colours["red"]+colours["reverse"]+colours["bold"]+"L'authentification à echouée... Veuillez réessayer."+colours["default"]
			elif ans == "2":
				register()
				log_in()
			elif ans == "99":
				print "Au revoir et a bientot !"
				connection_server.close()
				releve.running = False
				releve.join()
				sys.exit()

		else: #Des donnees de connexion ont ete trouvees.
			f = open("log_infos.pkl","r")
			U = pickle.Unpickler(f)
			datas = U.load()
			f.close()
			print "Données de connection trouvées . Tentative de connection avec les données de "+datas["user"]
			log_in(already_in = True, user = datas["user"], passwd = datas["passwd"], hash_512 = datas["hash"])
	else:
		connection_server.send(("CONNECT\\"+user+"\\"+hash_512+chr(23)))
		msg_from_server = attendre_reponse()
		if msg_from_server.split("\\")[0] == 'CONNECT' and msg_from_server.split("\\")[1] == "OK":
			print colours["green"]+colours["reverse"]+colours["bold"]+"Identification réussie !"+colours["default"]
			username = user
			mdp = passwd
		else :
			print colours["red"]+colours["reverse"]+colours["bold"]+"Les identifiants enregistrés semblent etre incorrects. Merci de saisir vos identifiants ci dessous."+colours["default"]
			os.remove("log_infos.pkl")
			log_in()

def trier_conv(fichier):
	conv = open(fichier,"r").read()
	messages = conv.split("\n")[:len(conv.split("\n"))-1]
	messages.sort()
	conv = open(fichier,"w")
	conv.write("\n".join(messages))
	conv.write("\n")
	conv.close()

def decrypter_conv(fichier, pwd, dest):
	#print "Params : \n\t-fichier : "+fichier+"\n\t-pwd : "+pwd+"\n\t-dest : "+dest
	f = open(fichier,"r")
	msg = f.read()
	f.close()
	if os.path.exists(pwd):
		passwdf = open(pwd, "r")
		passwd = passwdf.read()
		passwdf.close()
	else:
		passwd = pwd
	msg = msg.split("\n")
	decrypted = []
	for x in msg:
		if not x=="" or x == " ":
			xsplit = x.split("]")
			msg_decrypted = ucrpt.uncrypt_message("]".join(xsplit[1:]), passwd)
			decrypted.append("]".join([xsplit[0],msg_decrypted]))

	s = open(dest,'a')
	s.write("\n".join(decrypted)+"\n")
	s.close()
	os.remove(fichier)
	while os.path.exists(fichier):
		os.remove(fichier)

def inbox(already_in = False, conv_id = 0):
	global sender
	connection_server.send(("GET\\unreaded\\s_conv"+chr(23)))
	msg_from_server = attendre_reponse()
	if msg_from_server.split("\\")[0] == "GIVE" and msg_from_server.split("\\")[1] == "unreaded":
		nbr_convs = int(msg_from_server.split("\\")[3])
	if nbr_convs:
		for x in range(nbr_convs):
			connection_server.send(("GET\\unreaded\\s_conv\\"+str(x)+chr(23)))
			msg_from_server = attendre_reponse()
			if msg_from_server.split("\\")[0]=="KEY":
				verif_path(username+os.sep+"keys", folder = True)
				f = open(username+os.sep+"keys"+os.sep+msg_from_server.split("\\")[1]+"key",'w')
				f.write("\\".join(msg_from_server.split("\\")[2:]))
				f.close()
				msg_from_server = attendre_reponse()
			conv = open(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3]+"crypted",'w')
			conv.write("\\".join(msg_from_server.split("\\")[4:]))
			conv.close()
			decrypter_conv(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3]+"crypted",username+os.sep+"keys"+os.sep+msg_from_server.split("\\")[3]+"key", username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3])
			trier_conv(username+os.sep+"messages"+os.sep+msg_from_server.split("\\")[3])
	#Recuperation des groupes
	connection_server.send(("GET\\unreaded\\group"+chr(23)))
	msg_from_server = attendre_reponse()
	if msg_from_server.split("\\")[0] == "GIVE" and msg_from_server.split("\\")[1] == "unreaded":
		nbr_convs = int(msg_from_server.split("\\")[3])
		verif_path(username+os.sep+"datas"+os.sep+"groupsids.pkl")
		f = open(username+os.sep+"datas"+os.sep+"groupsids.pkl","r")
		Upckl = pickle.Unpickler(f)
		try:
			id_to_group = Upckl.load()
		except:
			id_to_group = {}
		f.close()
	if nbr_convs:
		for x in range(nbr_convs):
			i = 0
			print "Envoye : "+"GET\\unreaded\\group\\"+str(x)
			connection_server.send(("GET\\unreaded\\group\\"+str(x)+chr(23)))
			msg_from_server = attendre_reponse()
			if msg_from_server.split("\\")[0]=="INFOS":
				verif_path(username+os.sep+"groups"+os.sep+"infos"+os.sep+msg_from_server.split("\\")[1]+".info")
				verif_path(username+os.sep+"groups"+os.sep+"messages", True)
				key_file_name = username+os.sep+"groups"+os.sep+"infos"+os.sep+msg_from_server.split("\\")[1]+".info"
				f = open(key_file_name,'w')
				print "Fichier ouvert : "+key_file_name
				f.write("\n".join(msg_from_server.split("\\")[2:]))
				f.close()
				"""verif_path(username+os.sep+"datas"+os.sep+"groupsids.pkl")
				groupsids_f = open(username+os.sep+"datas"+os.sep+"groupsids.pkl", "r")
				try:
					groupsids = pickle.Unpickler(groupsids_f).load()
				except:
					groupsids = {}
				groupsids_f.close()"""
				id_to_group[msg_from_server.split("\\")[4].split("=")[1]] = msg_from_server.split("\\")[1]
				groupsids_f = open(username+os.sep+"datas"+os.sep+"groupsids.pkl", "w")
				pklgroupsids = pickle.Pickler(groupsids_f)
				pklgroupsids.dump(id_to_group)
				groupsids_f.close()

				msg_from_server = attendre_reponse()
			conv = open(username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]]+"crypted",'w')
			conv.write("\\".join(msg_from_server.split("\\")[4:]))
			conv.close()
			datas_f = open(username+os.sep+"groups"+os.sep+"infos"+os.sep+id_to_group[msg_from_server.split("\\")[3]]+".info", "r")
			datas = datas_f.read().split("\n")
			datas_f.close()
			decrypter_conv(username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]]+"crypted","=".join(datas[0].split("=")[1:]), username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]])
			trier_conv(username+os.sep+"groups"+os.sep+"messages"+os.sep+id_to_group[msg_from_server.split("\\")[3]])
	if not already_in:
		verif_path(username+os.sep+"messages", True)
		convs = os.listdir(username+os.sep+"messages")
		verif_path(username+os.sep+"groups"+os.sep+"messages", True)
		groups = os.listdir(username+os.sep+"groups"+os.sep+"messages")
		if len(convs) == 0 and len(groups)==0:
			print "Vous n'avez aucun message. Retour au Menu principal."
			afficher_menu()
			return 0
		menu_text = ""
		menu_text += "\n Veuillez entrer le numéro de la conversation que vous souhaitez visualiser :\n"+colours["yellow"]+colours["reverse"]+"[ 0 ] Retour au menu principal\n"+colours["default"]
		rep_available = ["0"]
		for x in range(len(convs)):
			menu_text += "[ "+str(x+1)+" ] "+ convs[x]+"\n"
			rep_available.append(str(x+1))
		for x in range(len(groups)):
			menu_text+="[ "+str(len(convs)+x+1)+" ] "+groups[x]+"\n"
			rep_available.append(str(len(convs)+x+1))
		menu_text += "\n"
		rep = verif_answer(menu_text,rep_available, "Non pris en charge... Réessayer.")
		if rep == "0":
			afficher_menu()
			return 0
	else:
		rep = conv_id
		convs = os.listdir(username+os.sep+"messages")
	if not int(rep) > len(convs):
		conv_type = "single"
		sender = convs[int(rep)-1]
		print "Voici votre conversation avec "+sender+"\n\n"
		f = open(username+os.sep+"messages"+os.sep+sender,'r')
		disc = f.read()
		f.close()
	else:
		conv_type = "group"
		groups = os.listdir(username+os.sep+"groups"+os.sep+"messages")
		group = groups[int(rep)-1-len(convs)]
		print "Voici le groupe "+group+"\n\n"
		f = open(username+os.sep+"groups"+os.sep+"messages"+os.sep+group, "r")
		disc = f.read()
		f.close()
	member_name_max_lenth = 4
	for x in disc.split("\n"):
		if not x == "" and len(x.split("]")[0].split("\\")[1]) > member_name_max_lenth and not x.split("]")[0].split("\\")[1] == username:
			member_name_max_lenth = len(x.split("]")[0].split("\\")[1])
		else:
			pass
	for x in disc.split("\n"):
		if x == "":
			continue
		if x.split("]")[0].split("\\")[1] == username:
			print colours["cyan"]+"Vous"+" "* (member_name_max_lenth - 4)+" : "+x.split("]")[1]+colours["default"]
		else :
			print colours["magenta"]+x.split("]")[0].split("\\")[1]+" "*(member_name_max_lenth - len(x.split("]")[0].split("\\")[1]))+" : "+x.split(']')[1]+colours["default"]
	rep_available = ["r","m"]
	choix = verif_answer("\nTaper r pour répondre, m pour retourner au menu précédent.", rep_available, "Valeur non prise en charge... Veuillez réessayer !")
	if choix == "r":
		if conv_type == "single" :
			envoyer_message(dest = sender, conv_type="single")
			inbox(already_in = True, conv_id = rep)
		else:
			envoyer_message(dest = group, conv_type="group")
			inbox(already_in = True, conv_id = rep)
	else:
		inbox()

def afficher_menu():
	if server_reachable:
		rep_available = ["1","99", "2","99+"]
		menu_text = "\nQue voulez-vous faire ?\n[1] Envoyer un message.\n[2] Accéder a ma boite de réception.\n"+"[99] Quitter l'application.\n"+colours["default"]+colours["red"]+colours["reverse"]+"[99+] Vous déconnecter et quitter l'application.\n"+colours["default"]
		rep = verif_answer(menu_text, rep_available, "Non pris en charge... Réessayer.")
		if rep == "1":
			envoyer_message()
		elif rep == "99" or rep == "99+":
			if rep == "99+":
				fichier = backup()
				if not fichier == "ERROR":
					while 1:
						try:
							shutil.rmtree(username)
							break
						except:
							pass
					os.remove("log_infos.pkl")
				else:
					pass
			releve.running = False
			connection_server.send("ASKQUITTING"+chr(23))
			releve.join()
			sys.exit()
		elif rep == "2":
			inbox()


def envoyer_message(dest = None, conv_type = None):

	if not dest:
		connection_server.send(("GET\\friends"+chr(23)))
		msg_from_server = attendre_reponse()
		print "Mes amis sont "+msg_from_server
		if msg_from_server == "GET\\friends\\REFUSED":
			print "Erreur lors de la récuperation de vos amis. Cela est probablement dut à une erreur dans votre connection. Solution proposee : rédemarer l'application et se reconnecter."
		else:
			msg_from_server = msg_from_server.split(", ")
			for x in msg_from_server:
				if x == " " or x == "":
					msg_from_server.remove(x)
			menu_text = ""
			menu_text += "\nVoici la liste de vos amis. Tapez leur numéro pour leur envoyer un message.\n"+colours["yellow"]+colours["reverse"]+"[ 0 ] Retour au menu principal\n"+colours["default"]
			rep_available = ["0", "G"]
			for x in range(len(msg_from_server)):
				menu_text += "[ "+str(x+1)+" ] "+msg_from_server[x]+"\n"
				rep_available.append(str(x+1))
			if len(rep_available) == 2 :
				menu_text += "Si tu n'as pas d'amis, prend un curly ;)\n"
			menu_text += colours["green"]+"[ + ]"+" Ajouter un ami.\n"+colours["default"]
			rep_available.append("+")
			if len(rep_available) > 3 :
				menu_text += colours["red"]+"[ - ]"+" Supprimer un ami.\n"+colours["default"]
				rep_available.append("-")
			menu_text += colours["blue"]+"[ G ] Créer un nouveau groupe.\n"+colours["default"]
			menu_text += "\n"
			rep = verif_answer(menu_text, rep_available, "Non pris en charge... Réessayer.")
			if rep == "+":
				friend_to_add = raw_input("Quel est le nom d'utilisateur de votre nouvel ami ? \nLaisser vide pour retourner au menu précédent. \n>>")
				if not len(friend_to_add)==0:
					connection_server.send(("ADD\\friend\\"+friend_to_add+chr(23)))
					msg_from_server = attendre_reponse()
					if msg_from_server == "ADD\\friend\\OK":
						print "Ami ajoute avec succes !"
					elif msg_from_server == "ADD\\friend\\404":
						print "Cet ami n'existe pas !"
					elif msg_from_server == "ADD\\friend\\REFUSED":
						print "Acces refuse !"
				elif len(friend_to_add) == 0:
					envoyer_message()
					return 0
			elif rep == "-":
				rep_available = []
				menu_text = ""
				menu_text += "Tapez le numéro de l'ami qui n'en est plus un : \n"+colours["yellow"]+colours["reverse"]+"[ 0 ] Retour en arriere\n"+colours["default"]
				for x in range(len(msg_from_server)):
					menu_text += "[ "+str(x+1)+" ] "+msg_from_server[x]+"\n"
					rep_available.append(str(x+1))
				rep_available.append("0")
				rep = verif_answer(menu_text, rep_available, "Valeur non prise en charge... Réessayez !")
				if rep == "0":
					envoyer_message()
					return 0
				connection_server.send(("REMOVE\\friend\\"+msg_from_server[int(rep)-1]+chr(23)))
				msg_from_server = attendre_reponse()
				if msg_from_server == "REMOVE\\friend\\OK":
					print "Ami supprimé avec succès"
				elif msg_from_server == "REMOVE\\friend\\404":
					print "Cet ami ne fait pas parti des votres !"
				elif msg_from_server == "REMOVE\\friend\\REFUSED":
					print "Acces refuse !"
			elif rep == "0":
				afficher_menu()
				return 0
			elif rep == "G":
				nom = raw_input("Donnez un nom à ce nouveau groupe.\nLaissez vide pour annuler et revenir en arriere.\n>>")
				if len(nom)==0:
					envoyer_message()
					return 0
				else:
					friends_to_add = []
					while True:
						menu_text = "Entrez le numéro de l'ami à ajouter au groupe.\n"+colours["yellow"]+colours["reverse"]+"[ 0 ] Annuler la création du groupe et retourner au menu précédent.\n"+colours["default"]
						rep_available = ["0"]
						if not len(friends_to_add) == 0:
							menu_text += colours["red"]+"[ - ] Retirer des amis déjà ajouté.\n"+colours["default"]
							rep_available.append("-")
						for x in range(len(msg_from_server)):
							if not msg_from_server[x] in friends_to_add:
								menu_text += "[ "+str(x+1)+" ] "+msg_from_server[x]+"\n"
								rep_available.append(str(x+1))
							else:
								menu_text += colours["green"]+"[ + ] "+msg_from_server[x]+"\n"+colours["default"]
						if len(friends_to_add)>1:
							menu_text+="[ "+str(len(msg_from_server)+1)+ " ] Valider et créer le groupe.\n"
							rep_available.append(str(len(msg_from_server)+1))
						rep = verif_answer(menu_text, rep_available, "Valeur non pris en charge... Réessayer.")
						if rep == "0":
							envoyer_message()
							return 0
						elif rep == "-":
							menu_text = "Entrez le numéro de l'ami qui ne doit pas être ajouté au groupe.\n"+colours["yellow"]+colours["reverse"]+"[ 0 ] Annuler et retourner au menu précédent.\n"+colours["default"]
							rep_available = ["0"]
							for x in range(len(friends_to_add)):
								menu_text += "[ "+str(x+1)+" ] "+friends_to_add[x]+"\n"
								rep_available.append(str(x+1))
							rep = verif_answer(menu_text, rep_available, "Non pris en charge... Réessayer.")
							friends_to_add.pop(int(rep)-1)
						elif rep==str(len(msg_from_server)+1):
							key = r_pass.generate(256)
							friends_to_add.append(username)
							connection_server.send("START\\group\\"+nom+"\\"+key+"\\"+str(len(friends_to_add))+"\\"+"\\".join(friends_to_add)+chr(23))
							msg_from_server = attendre_reponse()
							if msg_from_server.split("\\")[:2] == ["GROUP", "CREATED"]:
								print "Groupe créé avec succès."
								try:
									os.mkdir(username+os.sep+"groups")
								except:
									pass
								try:
									os.mkdir(username+os.sep+"groups"+os.sep+"infos")
								except :
									pass
								f=open(username+os.sep+"groups"+os.sep+"infos"+os.sep+nom+".info", "w")
								f.write("Key="+key+"\nMembers="+", ".join(friends_to_add)+"\nGroup id="+msg_from_server.split("\\")[2])
								f.close()
								break

						else:
							friends_to_add.append(msg_from_server[int(rep)-1])
			else:
				print msg_from_server[int(rep)-1],"selectionne."
				if not os.path.exists(username+os.sep+"messages"+os.sep+msg_from_server[int(rep)-1]):
					key = r_pass.generate(256)
					destinataire = msg_from_server[int(rep)-1]
					try:
						os.mkdir(username+os.sep+"keys")
					except:
						pass
					f = open(username+os.sep+"keys"+os.sep+destinataire+"key","w")
					f.write(key)
					f.close()
					connection_server.send("START\\s_conv\\"+msg_from_server[int(rep)-1]+"\\"+key+chr(23))
					msg_from_server = attendre_reponse()
					if msg_from_server == "S_CONV\\CREATED":
						print "Les messages de cette conversation seront chiffrés avec une clé unique."
					elif msg_from_server == "S_CONV\\REFUSED":
						print "ACCES REFUSE. Vous allez etre déconnecte."
						return 1
				else :
					destinataire = msg_from_server[int(rep)-1]
					f = open(username+os.sep+"keys"+os.sep+destinataire+"key","r")
					key = f.read()
					f.close()
				print "Tapez votre message ci dessous et appuyez sur entrée pour l'envoyer.\nLaissez le champ vide pour retrourner en arriere."
				message = raw_input(">>")
				if not len(message) == 0:
					msg_crypted = crpt.crypt_message(message, key)
					connection_server.send(("SEND\\"+destinataire+"\\"+msg_crypted+chr(23)))
					msg_from_server = attendre_reponse()
					if msg_from_server == "SEND\\OK":
						prev_conv = ""
						print "Message envoyé !\n\n"
						try:
							f = open(username+os.sep+"messages"+os.sep+destinataire,"r")
							prev_conv = f.read()
							f.close()
						except:
							pass
						finally:
							f = open(username+os.sep+"messages"+os.sep+destinataire,"w")
							f.write(prev_conv)
							f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+message+"\n")
							f.close()
							trier_conv(username+os.sep+"messages"+os.sep+destinataire)
				elif len(message) == 0 :
					envoyer_message()
					return 0

				else :
					print "Le message n'a pas été remis.\n\n"
		afficher_menu()
	else:
		if conv_type == "single":
			f = open(username+os.sep+"keys"+os.sep+dest+"key","r")
			key = f.read()
		else:
			f = open(username+os.sep+"groups"+os.sep+"infos"+os.sep+dest+".info")
			datas = f.read().split("\n")
			key = "=".join(datas[0].split("=")[1:])
			members = datas[1].split("=")[1].split(", ")
			id = datas[2].split("=")[1]

		f.close()
		print "Tapez votre message ci dessous et appuyez sur entré pour l'envoyer. Laissez le champ vide pour annuler et retourner à la conversation."
		message = raw_input(">>")
		if not len(message) == 0:
			msg_crypted = "["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+crpt.crypt_message(message, key)
			print "Message to send : "+msg_crypted
			if conv_type == "single":
				connection_server.send(("SEND\\"+dest+"\\"+msg_crypted+chr(23)))
			else:
				connection_server.send(("SEND_GROUP\\"+", ".join(members)+"\\"+id+"\\"+msg_crypted+chr(23)))
			msg_from_server = attendre_reponse()
			if msg_from_server == "SEND\\OK":
				prev_conv = ""
				print "Message envoyé !\n\n"
				try:
					if conv_type =="single":
						f = open(username+os.sep+"messages"+os.sep+dest,"r")
						prev_conv = f.read()
						f.close()
				except:
					pass
				finally:
					if conv_type == "single":
						f = open(username+os.sep+"messages"+os.sep+dest,"w")
						f.write(prev_conv)
						f.write("["+datetime.datetime.isoformat(datetime.datetime.now())+"\\"+username+"]"+message+"\n")
						f.close()
					if conv_type == "single":
						trier_conv(username+os.sep+"messages"+os.sep+dest)

			else :
				print "Le message n'a pas été remis.\n\n"
		else:
			return 0

def register():
	username = raw_input("Nom d'utilisateur : ")
	while not username :
		print "Le nom d'utilisateur ne doit pas etre vide... Veuillez réessayer !"
		username = raw_input("Nom d'utilisateur : ")
	passwd = ""
	passwd_conf = "a"
	while not passwd == passwd_conf:
		passwd = getpass.getpass("Mot de passe : ")
		while not passwd :
			print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
			passwd = getpass.getpass("Mot de passe : ")
		passwd_conf = getpass.getpass("Confirmation du mot de passe : ")
		while not passwd_conf :
			print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
			passwd_conf = getpass.getpass("Confirmation du mot de passe : ")
		if not passwd == passwd_conf:
			print "Les mots de passe ne correspondent pas... Veuillez réessayer !"
	email = raw_input("Email : ")
	while not email:
		print "L'email ne doit pas etre vide... Veuillez réessayer !"
		email = raw_input("Email : ")
	sha = hashlib.sha512((username+" : "+passwd).encode()).hexdigest()
	print "Creation de vos cles privees/publiques en cours (peut prendre quelques instants)"
	key = RSA.generate(4096)
	public_key = key.publickey()
	key_to_send = crpt.crypt_message(key.exportKey(format='PEM'), passwd)
	"""print "len(public_key) = "+str(len(public_key.exportKey()))
	print "len(private) = "+str(len(key.exportKey()))
	print "len crypted = "+str(len(key_to_send))
	print 'len both = '+str(len(public_key.exportKey())+len(key_to_send))
	print 'len esle = '+str(len("REGISTER\\"+"\\".join([username, sha, email])))
	print "len soustract = "+str(len("REGISTER\\"+"\\".join([username, sha, email, key_to_send, "\\".join(public_key.exportKey().split("\n"))])) - len("REGISTER\\"+"\\".join([username, sha, email])) - 2*len("\\"))
	msg_to_send = "REGISTER\\"+"\\".join([username, sha, email, key_to_send, "\\".join(public_key.exportKey().split("\n"))])
	print "Envoye : "+msg_to_send
	print "len envoye : "+str(len(msg_to_send.split("\\")))"""
	connection_server.send(("REGISTER\\"+"\\".join([username, sha, email, key_to_send, "\\".join(public_key.exportKey().split("\n"))])+chr(23)))
	msg_recu = attendre_reponse()
	if msg_recu == "REGISTER\\OK":
		print "Enregistement reussi !"
	elif msg_recu == "REGISTER\\ERROR":
		print "Something went wrong... Please try again !"
		sys.exit()
	elif msg_recu == "REGISTER\\USERNAME_ALREADY_EXISTS":
		print "Ce nom d'utilisateur est déja pris... Veuillez réessayer !"
		register()
	elif msg_recu == "REGISTER\\EMAIL_ALREADY_USED":
		print "Cette adresse mail à deja été utilisée... Veuillez réessayer !"
		register()

print "Connexion au serveur en cours...\r",

if __name__ == "__main__":
	args = parse_arguments()
	if args.hote:
		hote = args.hote
	if args.port:
		try:
			port = int(args.port)
			if not (port >= 1 and port <= 65535):
				raise ValueError
		except ValueError :
			print "Le port auquel se connecter doit être un nombre entier compris entre 1 et 65535"
			sys.exit()
	mainthread = threading.currentThread()
	server_reachable = True
	connection_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		connection_server.connect((hote, port))
	except:
		print "Le serveur est injoignable. Veuillez verifier votre connexion internet et reessayer. Si votre connexion est stable, et que le probleme persiste, il est probable que le serveur soit hors ligne et nous vous suggerons de patienter jusqu'a ce qu'il soit remis en service. Merci."
		sys.exit()

	verrou = threading.RLock()

	releve = Releve()
	releve.start()

	username = ""
	sender = ""
	mdp = ""
	private_key = ""



	log_in()
	afficher_menu()
