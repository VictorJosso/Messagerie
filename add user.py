# -*- coding: utf-8 -*-
"""Code par Victor Josso"""
import pickle
import os
import getpass
import hashlib
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Permet d'ajouter des utilisateurs à la messagerie.")
    parser.add_argument("-u", "--username", help = "Spécifie un nom d'utilisateur.")
    parser.add_argument("-s", "--sha512", help = "Spécifie le hash sha512 correspondant à l'utilisateur")
    parser.add_argument("-e", "--email", help = "Spécifie une adresse email.")
    return  parser.parse_args()



paths_to_add = ["clients", "clients/Backups", "clients/datas", "clients/convert-tables", "clients/Keys", "clients/groups", "clients/messages"]
for path in paths_to_add:
    try:
        os.mkdir(path)
    except:
        pass

os.system("touch clients/convert-tables/mails")
os.system("touch clients/convert-tables/users_ids")
os.system("touch clients/convert-tables/users")

args = parse_arguments()
username = args.username
identifiant = str(len(os.listdir("clients/datas"))+1)
while not len(identifiant) == 10:
    identifiant = "0"+identifiant

mail = args.email

filename = args.sha512

f = open("clients/datas/"+filename,'w')
f.write("username = "+username+"\n")
f.write("email = "+mail+"\n")
f.write("email_verified = False\n")
f.write("id = "+identifiant+"\n")
f.write("friends =  ")
f.close()

f = open("clients/convert-tables/users", "a")
f.write(username+"\n")
f.close()

f = open("clients/convert-tables/mails", "a")
f.write(mail+"\n")
f.close()

os.mkdir("clients/messages/"+username)
os.mkdir("clients/Backups/"+username)
os.mkdir("clients/Keys/"+username)
os.mkdir("clients/groups/"+username)

f = open("clients/convert-tables/users_ids","r")
u = pickle.Unpickler(f)
try:
    table = u.load()
except:
    table = {}
f.close()
table[username]=identifiant
f = open("clients/convert-tables/users_ids","w")
p = pickle.Pickler(f)
p.dump(table)
f.close()
