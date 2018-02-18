import pickle
import os
import getpass
import hashlib
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Permet d'ajouter des utilisateurs a la messagerie.")
    parser.add_argument("-u", "--username", help = "Specifie un nom d'utilisateur.")
    parser.add_argument("-s", "--sha512", help = "Specifie le hash sha512 correspondant a l'utilisateur")
    parser.add_argument("-e", "--email", help = "Specifie une adresse email.")
    return  parser.parse_args()

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
