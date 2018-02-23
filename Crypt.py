# -*- coding: utf-8 -*-
"""Code par Victor Josso"""

from getpass import getpass
import binascii
import os


def crypt(fichier, password):
    f=open(fichier,"rb")
    text = f.read()
    f.close()
    text = bin(int(binascii.hexlify(text), 16))[2:]
    pass_crypt = bin(int(binascii.hexlify(password), 16))[2:]
    texte_chiffre = ""
    tabl_buffer = []
    toursafaire = len(text)
    for x in range(len(text)):
        bit_t = text[x]
        bit_p = pass_crypt[x%len(pass_crypt)]
        bit_c = str((int(bit_p)+int(bit_t))%2)
        tabl_buffer.append(bit_c)

    compteur = 0
    for x in tabl_buffer:
        if x == "0":
            compteur+=1
        else:
            break
    texte_chiffre = hex(int('0b'+"".join(tabl_buffer), 2))
    texte_chiffre = texte_chiffre[2:len(texte_chiffre)-1]
    if len(texte_chiffre)%2==1:
        texte_chiffre = "0"+texte_chiffre
    texte_chiffre = binascii.unhexlify(texte_chiffre)
    name = fichier.split("\\")[len(fichier.split("\\"))-1]
    name = name.split('.')
    if len(name) == 1:
        name = fichier + ".secure"
        file_type = None
    else:
        file_type = name[len(name)-1]
        name = "\\".join(fichier.split("\\")[:len(fichier.split("\\"))-1])+"\\"+".".join(name[:len(name)-1])+"-"+name[len(name)-1]+".secure"
    f = open(fichier, "wb")
    f.write("Original file type : "+str(file_type)+"\n")
    f.write(str(compteur)+"\n")
    f.write(texte_chiffre)
    f.close()
    return fichier


def crypt_message(message, password):
    text = message
    text = bin(int(binascii.hexlify(text), 16))[2:]
    pass_crypt = bin(int(binascii.hexlify(password), 16))[2:]
    texte_chiffre = ""
    tabl_buffer = []
    toursafaire = len(text)
    for x in range(len(text)):
        bit_t = text[x]
        bit_p = pass_crypt[x%len(pass_crypt)]
        bit_c = str((int(bit_p)+int(bit_t))%2)
        tabl_buffer.append(bit_c)

    compteur = 0
    for x in tabl_buffer:
        if x == "0":
            compteur+=1
        else:
            break
    texte_chiffre = hex(int('0b'+"".join(tabl_buffer), 2))
    texte_chiffre = texte_chiffre[2:len(texte_chiffre)-1]
    if len(texte_chiffre)%2==1:
        texte_chiffre = "0"+texte_chiffre
    #texte_chiffre = binascii.unhexlify(texte_chiffre)
    return str(compteur)+"/"+texte_chiffre

def verif_path(path):
    try:
        open(path, 'r')
        return True
    except IOError:
        return False

def setup(path_given = False):
    if not path_given :
        fichier = raw_input("Quel est le chemin d'acces au fichier à chiffrer ? > ")
        while not verif_path(fichier):
            print "Ce fichier est introuvable... Veuillez reessayer !"
            fichier = raw_input("Quel est le chemin d'acces au fichier à chiffrer ? > ")
        mdp = getpass("Veuillez saisir le mot de passe a utiliser pour chiffer le document > ")
        while not mdp:
            print "Le mot de passe ne doit pas etre vide... Veuillez reessayer !"
            mdp  = getpass("Veuillez saisir le mot de passe à utiliser pour chiffrer le document > ")
        return fichier, mdp
    else:
        mdp = getpass("Veuillez saisir le mot de passe à utiliser pour chiffrer le document > ")
        while not mdp:
            print "Le mot de passe ne doit pas etre vide... Veuillez réessayer !"
            mdp  = getpass("Veuillez saisir le mot de passe a utiliser pour chiffrer le document > ")
        return mdp


if __name__ == "__main__":
    fichier, mdp = setup()
    crypt(fichier, mdp)
