#!/usr/bin/env python
# -*- coding utf-8 -*-
from __future__ import with_statement
from subprocess import call as runCommand
from subprocess import check_output as cout
from subprocess import Popen as popen
#from twatch import *
import web,requests,json,redis,re,time,urllib,threading
import os,sys,socket,fcntl,struct,shelve,datetime,hashlib
import settings
from scripts import action

#Methods to get interface data
def get_interface_ip(ifname):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def get_lan_ip():
  ip = socket.gethostbyname(socket.gethostname())
  if ip.startswith("127.") and os.name != "nt":
    interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "wifi0", "ath0", "ath1", "ppp0",]
    for ifname in interfaces:
      try:
        ip = get_interface_ip(ifname)
        break
      except IOError: pass
  return ip

#Helper methods

def downloadTorrent(url):
  timestamp = int(time.time())
  req = requests.get(url,stream=True)
  with open('%s/tfile_%d.torrent'%(settings.TORRENTS_DIR,timestamp),'wb') as f:  
      for chunk in req.iter_content(256):
        f.write(chunk)

def checktype(f):
  typ = "file"
  if os.path.isdir(f): typ = "dir"
  elif reduce(lambda x,y:x|y, map(lambda x: x in f, ('mp4','ogv','webm','avi','mkv'))):
    typ = 'mov'
  elif reduce(lambda x,y:x|y, map(lambda x: x in f, ('jpg','png','gif','jpeg'))):
    typ = 'pic'
  return typ

urls = (
  '/torrentor',             'Main',
  '/torrentor/',            'Main',
  '/torrentor/q/',          'Query',
  '/torrentor/l/(.*)',      'List',
  '/torrentor/media:(.+)/', 'Media',
  #json views
  '/torrentor/json:(.+)/',  'JSON',
  '/torrentor/json:(.+)/(.+)',  'JSON'
)

r = redis.StrictRedis(host='localhost', port=6379, db=0)
render = web.template.render(settings.TEMPLATES_DIR)
app = web.application(urls, globals())

class Main:
  def GET(self):
    f = open('%s/templates/index.tfs'%settings.SITE_DIR,'r')
    data = f.read()
    f.close()
    return data
    #return render.index()
  def POST(self):
    return render.index()

class Media:
  def GET(self,path):
      return render.media(path.split('/')[-1],path,path[:-3]+'srt')

class Query:
  def GET(self):
    f = open('%s/templates/list.tfs'%settings.SITE_DIR,'r')
    data = f.read().decode('utf-8').replace('<PATH>',"/")
    f.close()
    return data
  def POST(self):
    query = web.input().query
    if re.match('(magnet:\?.*|http(s|)://.*/.*\.(torrent\?title=.*|torrent))',query):
      timestamp = int(time.time())
      req = requests.get(query,stream=True)
      with open('%s/tfile_%d.torrent'%(settings.TORRENTS_DIR,timestamp),'wb') as f:  
          for chunk in req.iter_content(256):
            f.write(chunk)
      return web.redirect('/torrentor/')
    else:
      if query == '': return web.redirect('/torrentor/l/')
      path = settings.MEDIA_DIR
      files = sorted([(e,checktype("%s/%s"%(path,e))) for e in os.listdir(path) if query.lower() in e.decode('utf-8').lower() and e[-3:]!='srt'], key=lambda e:os.path.getctime(path+'/'+e[0]), reverse=True)
      return render.list(query,files,False)

class List:
  def GET(self,path):
    f = open('%s/templates/list.tfs'%settings.SITE_DIR,'r')
    data = f.read().decode('utf-8').replace('<PATH>',path)
    f.close()
    return data
  def POST(self):
    f = open('%s/templates/list.tfs'%settings.SITE_DIR,'r')
    data = f.read().decode('utf-8').replace('<PATH>',path)
    f.close()
    return data

class JSON:
  def GET(self,call,arg=""): 
    if call == 'status':
      try:
        omxcount = int(cout(["pgrep","-f","omxplayer","-c"]))
      except: omxcount = 0
      if omxcount==0: 
          action.stop()
      retval = action.show_list()
      return retval
    if call == 'toggle':
      return action.toggle(arg)

  def POST(self,call):
    web.header('Content-Type', 'application/json')
    post = json.loads(web.data())
    if call == 'match':
      query = post["query"];
      if re.match('(magnet:\?.*|http(s|)://.*/.*\.(torrent\?title=.*|torrent))',query):
        downloadTorrent(query)
        return '{"status":"downloading"}'
      else:
          found = [e for e in os.listdir(settings.MEDIA_DIR) if query in e]
          if(found): return '{"status":"found"}'
          else: 
            try:
              data = {'results':requests.get('http://fenopy.se/module/search/api.php?keyword=%s&format=json&limit=5'%query).json()}
              data.update(status="search")
              return json.dumps(data)
            except: return '{"status":"error"}'
    if call == 'convert':
       convThread = threading.Thread(target=action.convert,args=(settings.MEDIA_DIR+'/'+post['path'],))
       convThread.start()
       convThread.join()
       return('{"error":false,"status":"added to conversion queue"}')
    if call == 'playHDMI':
      #runCommand('echo "on 0" | cec-client -s',shell=True)
      runCommand(["screen", "-S", "omx", "-X", "quit"])
      popen(["screen", "-dmS", "omx", "omxplayer", "-o", "hdmi", "%s/%s"%(settings.MEDIA_DIR,post['path'])])
      action.play(post['path'].split('/')[-1])
      return('{"error":false,"status":"playing"}')
    if call == 'control':
      keymap = {'back':'\c[[B', 'play':'p', 'stop':'q', 'next':'\c[[A'}
      runCommand(["screen", "-S", "omx", "-X", "stuff", keymap[post['directive']]])
    if call == 'subtitle':
      try:
        f = open(("%s/%s"%(settings.MEDIA_DIR,post['path']))[:-3]+'srt')
        result = "true"
        f.close()
      except IOError:
        action.get_subtitle("%s/%s"%(settings.MEDIA_DIR,post['path'])) 
        try:
          f = open(("%s/%s"%(settings.MEDIA_DIR,post['path']))[:-3]+'srt')
          result = "true"
          f.close()
        except IOError:
          result = "false"
      return '{"result":%s}'%result
    if call == 'list':
      path = post['path']
      abs_path = "%s/%s"%(settings.MEDIA_DIR,path.strip("/"))
      if(os.path.isdir(abs_path)):
        if path in '/': path = '/' 
        if r.exists(path):
            data = json.loads(r.get(path))
            data.update(cached=True)
            data = json.dumps(data)
        else:
            if path == '/' :
              files = sorted([(e, checktype("%s/%s"%(abs_path,e))) for e in os.listdir(abs_path) if e[-3:] not in ('srt','cnva')], key=lambda e:os.path.getctime(abs_path+'/'+e[0]), reverse=True)
            else:
              files = [(e.replace("'","&#39;"), checktype("%s/%s"%(abs_path,e))) for e in os.listdir(abs_path) if e[-3:] not in ('cnva','srt')]
            data = '{"path":"%s","files":%s,"type":"dir","indexing":true}'%(path,json.dumps(files))
            r.set(path,data)
            r.expire(path,3000)
        return data
      else:
        return '{"path":"%s", "type":"file","indexing":false}'%(path)
    return '{"error":true,"type":"InvalidCallError","call":"%s"}'%call


if __name__ == '__main__':
  #sys.argv.append("%s:8092"%get_lan_ip())
  app.internalerror = web.debugerror
  web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
  app.run()
