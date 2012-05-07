import re
import tornado.web
import redis
import os
from base64 import b64encode,b64decode

from util.encode import encode,decode,key
from util.getby import get_domain_by_name

from db.redis.user_follow_graph import UserFollowGraph
from db.redis.user_activity_graph import UserActivityGraph

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def rd(self):
        return redis.StrictRedis(host='localhost', port=6379, db=0)

    @property
    def uag(self):
        return UserActivityGraph(self.rd)

    @property
    def ufg(self):
        return UserFollowGraph(self.rd)
    
    def avatar(self, avasize, user_id, uuid):
        shard = str(user_id % 40)
        avapath = "".join(["usrimg/", shard, "/", avasize, "_", uuid, ".jpg"])
        if os.path.exists("/work/Dormforge/static/" + avapath):
            avatarpath = avapath
        else:
            avatarpath = "".join(["img/", avasize, "_noavatar.jpg"])
        return self.static_url(avatarpath)
        #return "/static/" + avatarpath

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: return None
        return self.db.get("SELECT * FROM fd_People WHERE id = %s", int(user_id))

    def set_default_headers(self): 
        self.set_header('Server', '18zhouServer/1.1')

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render("404.html")
        elif status_code == 500:
            self.render("500.html")

    def encode(self, unicodeString):  
        strorg = unicodeString.encode('utf-8')  
        strlength = len(strorg)  
        baselength = len(key)  
        hh = []  
        for i in range(strlength):  
            hh.append(chr((ord(strorg[i])+ord(key[i % baselength]))%256))  
        return b64encode(''.join(hh)).encode("hex")

    def at(self, value):
        ms = re.findall(u'(@[\u4e00-\u9fa5A-Za-z0-9_-]{2,16})', value)
        if (len(ms) > 0):
            for m in ms:
                username = m[1:]
                domain = get_domain_by_name(self.db, self.rd, username)
                if domain:
                    value = value.replace(m, '@<a href="/people/' + domain + '">' + username + '</a>')
        return value

    def br(self, value):
        return value.replace("\n", "<br>")
