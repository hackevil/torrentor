from __future__ import with_statement
import os,sys

content = ""
BASE_DIR = os.getcwd()
print "BASE_DIR:",BASE_DIR
HOME_DIR = ospath..expanduser("~")
print "HOME_DIR:",HOME_DIR

with open('runapps.sh','r') as f:
  content = f.read()
with open('runapps.sh','w+') as f:
  f.write(content.replace('<BASE_DIR>',BASE_DIR))

with open('settings.py','r') as f:
  content = f.read()
with open('settings.py','w+') as f:
  f.write(content.replace('<BASE_DIR>',BASE_DIR))

with open('rtorrent.rc','r') as f:
  content = f.read()
with open('%s/.rtorrent.rc'%HOME_DIR,'w+') as f:
  f.write(content.replace('<BASE_DIR',BASE_DIR))



