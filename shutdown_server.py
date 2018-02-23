import hashlib
import getpass

pwd = getpass.getpass("Veuillez entrer la clef de securite ici : ")
f = open("shutdown",'w')
f.write(pwd)
f.close()
