#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os.path
import sys
import re
import string
import time
import uuid
import binascii
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import logging
import redis
import tempfile
import shutil

from tornado.options import define, options
from tornado.escape import linkify
from util.encrypt import encrypt_password,validate_password
from util.getby import get_id_by_name,get_domain_by_name
from util.encode import encode,decode,key
from util.redis_activity import add_activity,del_activity
from db.redis.user_follow_graph import UserFollowGraph
from db.redis.user_activity_graph import UserActivityGraph
from base64 import b64encode,b64decode
from PIL import Image

define("port", default=8080, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="df", help="blog database name")
define("mysql_user", default="df", help="blog database user")
define("mysql_password", default="df", help="blog database password")

reload(sys)
sys.setdefaultencoding('utf-8')

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", HomeHandler),
                (r"/my", MyhomeHandler),
                (r"/signup", SignupHandler),
                (r"/login", LoginHandler),
                (r"/logout", LogoutHandler),
                (r"/contact", ContactHandler),
                (r"/about", AboutHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)", PeopleHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)/following", FollowingHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)/follower", FollowerHandler),
                (r"/(city|college|major)/(.*)", RegionHandler),
                (r"/isexist", ExistHandler),
                (r"/follow", FollowHandler),
                (r"/unfollow", UnfollowHandler),
                (r"/selfdesc", SelfdescHandler),
                (r"/pubstatus", PubstatusHandler),
                (r"/deleteactivity", DeleteActivityHandler),
                (r"/status/edit", EditstatusHandler),
                (r"/status/([0-9a-z]+)", StatusHandler),
                (r"/note/touch", PubnoteHandler),
                (r"/viewnote", ViewnoteHandler),
                (r"/note/([0-9a-z]+)", NoteHandler),
                (r"/settings/(account|avatar|passwd|delete)", SettingsHandler),
                (r"/link/edit", EditlinkHandler),
                (r"/link/([0-9a-z]+)", LinkHandler),
                (r"/cansug", CansugHandler),
                (r"/doc/edit", EditdocHandler),
                (r"/doc/([0-9a-z]+)", DocHandler),
                (r"/more/([a-z]+)", MoreHandler),
                (r".*", PNFHandler),
                ]
        settings = dict(
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                ui_modules={"Setting": SettingModule},
                xsrf_cookies=True,
                cookie_secret="18oETzKXQAGaYdkL5gEmGEJJFuYh7ENnpTXdTP1o/Vo=",
                login_url="/login",
                autoescape=None,
                )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = tornado.database.Connection(
                host=options.mysql_host, database=options.mysql_database,
                user=options.mysql_user, password=options.mysql_password)

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

class FollowBaseHandler(BaseHandler):
    def follow(self, domain, follow_type):
        people = self.db.get("SELECT id,name,domain,uuid_ FROM fd_People WHERE domain = %s", domain) 
        if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        if not self.current_user or self.current_user and self.current_user.id != people.id:
            template_values['is_self'] = False
        else:
            template_values['is_self'] = True
        if template_values['is_self'] and follow_type == "following":
            page_title = "我关注的人"
        elif template_values['is_self'] and follow_type == 'follower':
            page_title = "关注我的人"
        elif not template_values['is_self'] and follow_type == 'following':
            page_title = "".join([people.name, "关注的人"])
        elif not template_values['is_self'] and follow_type == 'follower':
            page_title = "".join(["关注", people.name, "的人"])
        template_values['page_title'] = page_title
        template_values['id'] = people.id
        template_values['uuid'] = people.uuid_
        template_values['username'] = people.name
        template_values['domain'] = people.domain
        template_values['image'] = self.avatar("xl", people.id, people.uuid_)
        template_values['follow_count'] = self.ufg.follow_count(people.id)
        template_values['follower_count'] = self.ufg.follower_count(people.id)
        template_values['is_follow'] = self.ufg.is_follow(self.current_user.id, people.id) if self.current_user else False
        if follow_type == 'following':
            follows = self.ufg.get_follows(template_values['id'])
        elif follow_type == 'follower':
            follows = self.ufg.get_followers(template_values['id'])
        if len(follows) == 0:
            follow_people = []
        else:
            for i in range(len(follows)):
                follows[i] = int(follows[i])
            if len(follows) == 1:
                follow_people = self.db.query("SELECT id,name,domain,uuid_ from fd_People where id = %s", follows[0]) 
            else:
                orderstr = str(follows)[1:-1].replace(" ","")
                follow_people = self.db.query("SELECT id,name,domain,uuid_ from fd_People where id in %s order by find_in_set(id, %s)", tuple(follows), orderstr) 
            for i in range(len(follow_people)):
                follow_people[i].is_follow = self.ufg.is_follow(self.current_user.id, follow_people[i].id) if self.current_user else False
                follow_people[i].image = self.avatar("m", follow_people[i].id, follow_people[i].uuid_)
                if not self.current_user or self.current_user and self.current_user.id != follow_people[i].id:
                    follow_people[i].is_self = False 
                else:
                    follow_people[i].is_self = True
        template_values['follow'] = follow_people 
        template_values['type'] = follow_type 
        return template_values

class HomeHandler(BaseHandler):
    def get(self):
        if self.current_user:
            template_values = {}
            template_values['all_activities'] = self.uag.get_all_activities(self.db, 0)
            template_values['lastindex'] = 20
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= self.uag.count_all_activity():
                template_values['hasnext'] = 0
            self.render("home.html", template_values=template_values)
        else:
            self.render("index.html")

class MyhomeHandler(BaseHandler):
    def get(self):
        if self.current_user:
            template_values = {}
            template_values['all_activities'] = self.uag.get_my_activities(self.db, self.current_user.id, 0)
            template_values['lastindex'] = 20
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= self.uag.count_my_activity(self.current_user.id):
                template_values['hasnext'] = 0
            self.render("myhome.html", template_values=template_values)
        else:
            self.render("index.html")

class MoreHandler(BaseHandler):
    def get(self, prop):
        template_values = {}
        if prop in ["home", "myhome"]:
            startindex = self.get_argument("lastindex")
            if prop == "home":
                template_values['all_activities'] = self.uag.get_all_activities(self.db, int(startindex))
            elif prop == "myhome":
                template_values['all_activities'] = self.uag.get_my_activities(self.db, self.current_user.id, int(startindex))
            template_values['lastindex'] = int(startindex) + 20
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= self.uag.count_all_activity():
                template_values['hasnext'] = 0
            self.render("modules/activities.html", template_values=template_values)

class SignupHandler(BaseHandler):
    def get(self):
        if self.current_user:
            return self.redirect("/")
        self.render("signup.html", template_values={})

    def post(self):
        template_values = {}
        errors = 0
        #username verify
        username_error = 0
        username_error_messages = ['',
                u'请输入用户名',
                u'用户名不能超过16个字符',
                u'用户名不能少于2个字符',
                u'已被占用']
        username = self.get_argument("username").strip()
        if len(username) == 0:
            errors = errors + 1
            username_error = 1
        else:
            if len(username) > 16:
                errors = errors + 1
                username_error = 2
            else:
                if len(username) < 2:
                    errors = errors + 1
                    username_error = 3
                else:
                    user_id = self.db.get("select id from fd_People where name = %s", username)
                    if(user_id):
                        errors = errors + 1
                        username_error = 4 
        template_values['username'] = username
        template_values['username_error'] = username_error
        template_values['username_error_message'] = username_error_messages[username_error]
        #password verify
        password_error = 0
        password_error_messages = ['',
                u'请输入密码',
                u'密码长度不能超过 32 个字符',
                u'两次输入的密码不一致']
        password = self.get_argument("password").strip()
        password_again = self.get_argument("password_again").strip()
        if len(password) == 0:
            errors = errors + 1
            password_error = 1
        else:
            if len(password) > 32:
                errors = errors + 1
                password_error = 2
            else:
                if(password != password_again):
                    errors = errors + 1
                    password_error = 3
        template_values['password'] = password
        template_values['password_again'] = password_again
        template_values['password_error'] = password_error
        template_values['password_error_message'] = password_error_messages[password_error]
        #email verify
        email_error = 0
        email_error_messages = ['',
                u'请输入你的邮箱',
                u'邮箱长度不能超过32个字符',
                u'你输入的邮箱不符合规则',
                u'该邮箱已被人注册']
        email = self.get_argument("email").strip()
        if len(email) == 0:
            errors = errors + 1
            email_error = 1
        else:
            if len(email) > 32:
                errors = errors + 1
                email_error = 2
            else:
                p = re.compile(r"(?:^|\s)[-a-z0-9_.+]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)", re.IGNORECASE)
                if p.search(email):
                    user_id = self.db.get("select id from fd_People where email = %s", email)
                    if user_id:
                        errors = errors + 1
                        email_error = 4
                else:
                    errors = errors + 1
                    email_error = 3
        template_values['email'] = email
        template_values['email_error'] = email_error
        template_values['email_error_message'] = email_error_messages[email_error]
        #college&major verify
        coltype = self.get_argument("coltype").strip()
        if coltype == 'bk':
            college_error = 0
            college_error_messages = ['',
                    u'请输入学校全称',
                    u'学校不存在或不是全称']
            college = self.get_argument("bkbkcollege").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            else:
                college_id = self.db.get("select id from fd_College where name = %s", college)
                if not college_id:
                    errors = errors + 1
                    college_error = 2
            template_values['coltype'] = coltype
            template_values['bkbkcollege'] = college
            template_values['bkbkcollege_error'] = college_error
            template_values['bkbkcollege_error_message'] = college_error_messages[college_error]

            major_error = 0
            major_error_messages = ['',
                    u'请输入专业全称',
                    u'请输入正确的专业全称']
            major = self.get_argument("bkbkmajor").strip()
            if len(major) == 0:
                errors = errors + 1
                major_error = 1
            else:
                if len(major) < 2 or len(major) > 50:
                    errors = errors + 1
                    major_error = 2
            template_values['bkbkmajor'] = major
            template_values['bkbkmajor_error'] = major_error
            template_values['bkbkmajor_error_message'] = major_error_messages[major_error]
        if coltype == 'ss':
            college_error = 0
            college_error_messages = ['',
                    u'请输入硕士学校全称',
                    u'学校不存在或不是全称']
            college = self.get_argument("sssscollege").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            else:
                college_id = self.db.get("select id from fd_College where name = %s", college)
                if not college_id:
                    errors = errors + 1
                    college_error = 2
            template_values['coltype'] = coltype
            template_values['sssscollege'] = college
            template_values['sssscollege_error'] = college_error
            template_values['sssscollege_error_message'] = college_error_messages[college_error]

            major_error = 0
            major_error_messages = ['',
                    u'请输入硕士专业全称',
                    u'请输入正确的硕士专业全称']
            major = self.get_argument("ssssmajor").strip()
            if len(major) == 0:
                errors = errors + 1
                major_error = 1
            else:
                if len(major) < 2 or len(major) > 50:
                    errors = errors + 1
                    major_error = 2
            template_values['ssssmajor'] = major
            template_values['ssssmajor_error'] = major_error
            template_values['ssssmajor_error_message'] = major_error_messages[major_error]

            college_error = 0
            college_error_messages = ['',
                    u'请输入本科学校全称',
                    u'学校不存在或不是全称']
            college = self.get_argument("ssbkcollege").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            else:
                college_id = self.db.get("select id from fd_College where name = %s", college)
                if not college_id:
                    errors = errors + 1
                    college_error = 2
            template_values['coltype'] = coltype
            template_values['ssbkcollege'] = college
            template_values['ssbkcollege_error'] = college_error
            template_values['ssbkcollege_error_message'] = college_error_messages[college_error]

            major_error = 0
            major_error_messages = ['',
                    u'请输入本科专业全称',
                    u'请输入正确的本科专业全称']
            major = self.get_argument("ssbkmajor").strip()
            if len(major) == 0:
                errors = errors + 1
                major_error = 1
            else:
                if len(major) < 2 or len(major) > 50:
                    errors = errors + 1
                    major_error = 2
            template_values['ssbkmajor'] = major
            template_values['ssbkmajor_error'] = major_error
            template_values['ssbkmajor_error_message'] = major_error_messages[major_error]
        if coltype == 'bs':
            college_error = 0
            college_error_messages = ['',
                    u'请输入博士学校全称',
                    u'学校不存在或不是全称']
            college = self.get_argument("bsbscollege").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            else:
                college_id = self.db.get("select id from fd_College where name = %s", college)
                if not college_id:
                    errors = errors + 1
                    college_error = 2
            template_values['coltype'] = coltype
            template_values['bsbscollege'] = college
            template_values['bsbscollege_error'] = college_error
            template_values['bsbscollege_error_message'] = college_error_messages[college_error]

            major_error = 0
            major_error_messages = ['',
                    u'请输入博士专业全称',
                    u'请输入正确的博士专业全称']
            major = self.get_argument("bsbsmajor").strip()
            if len(major) == 0:
                errors = errors + 1
                major_error = 1
            else:
                if len(major) < 2 or len(major) > 50:
                    errors = errors + 1
                    major_error = 2
            template_values['bsbsmajor'] = major
            template_values['bsbsmajor_error'] = major_error
            template_values['bsbsmajor_error_message'] = major_error_messages[major_error]

            college_error = 0
            college_error_messages = ['',
                    u'请输入硕士学校全称',
                    u'学校不存在或不是全称']
            college = self.get_argument("bssscollege").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            else:
                college_id = self.db.get("select id from fd_College where name = %s", college)
                if not college_id:
                    errors = errors + 1
                    college_error = 2
            template_values['coltype'] = coltype
            template_values['bssscollege'] = college
            template_values['bssscollege_error'] = college_error
            template_values['bssscollege_error_message'] = college_error_messages[college_error]

            major_error = 0
            major_error_messages = ['',
                    u'请输入硕士专业全称',
                    u'请输入正确的硕士专业全称']
            major = self.get_argument("bsssmajor").strip()
            if len(major) == 0:
                errors = errors + 1
                major_error = 1
            else:
                if len(major) < 2 or len(major) > 50:
                    errors = errors + 1
                    major_error = 2
            template_values['bsssmajor'] = major
            template_values['bsssmajor_error'] = major_error
            template_values['bsssmajor_error_message'] = major_error_messages[major_error]

            college_error = 0
            college_error_messages = ['',
                    u'请输入本科学校全称',
                    u'学校不存在或不是全称']
            college = self.get_argument("bsbkcollege").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            else:
                college_id = self.db.get("select id from fd_College where name = %s", college)
                if not college_id:
                    errors = errors + 1
                    college_error = 2
            template_values['coltype'] = coltype
            template_values['bsbkcollege'] = college
            template_values['bsbkcollege_error'] = college_error
            template_values['bsbkcollege_error_message'] = college_error_messages[college_error]

            major_error = 0
            major_error_messages = ['',
                    u'请输入本科专业全称',
                    u'请输入正确的本科专业全称']
            major = self.get_argument("bsbkmajor").strip()
            if len(major) == 0:
                errors = errors + 1
                major_error = 1
            else:
                if len(major) < 2 or len(major) > 50:
                    errors = errors + 1
                    major_error = 2
            template_values['bsbkmajor'] = major
            template_values['bsbkmajor_error'] = major_error
            template_values['bsbkmajor_error_message'] = major_error_messages[major_error]
        if coltype == 'zx':
            college_error = 0
            college_error_messages = ['',
                    u'请输入学校全称']
            college = self.get_argument("zxschool").strip()
            if len(college) == 0:
                errors = errors + 1
                college_error = 1
            template_values['coltype'] = coltype
            template_values['zxschool'] = college
            template_values['zxschool_error'] = college_error
            template_values['zxschool_error_message'] = college_error_messages[college_error]

            province_error = 0
            province_error_messages = ['',
                    u'请输入省份',
                    u'不存在该省份']
            province = self.get_argument("zxprovince").strip()
            if len(province) == 0:
                errors = errors + 1
                major_error = 1
            else:
                province_id = self.db.get("select id from fd_Province where name = %s", province)
                if not province_id:
                    errors = errors + 1
                    province_error = 2
            template_values['zxprovince'] = province
            template_values['zxprovince_error'] = province_error
            template_values['zxprovince_error_message'] = province_error_messages[province_error]

            city_error = 0
            city_error_messages = ['',
                    u'请输入城市']
            city = self.get_argument("zxcity").strip()
            if len(city) == 0:
                errors = errors + 1
                major_error = 1
            template_values['zxcity'] = city
            template_values['zxcity_error'] = city_error
            template_values['zxcity_error_message'] = city_error_messages[city_error]
        #domain verify
        domain_error = 0
        domain_error_messages = ['',
                u'请输入个性域名',
                u'个性域名不能超过16个字符',
                u'个性域名不能少于2个字符',
                u'个性域名不符合规则，请使用a-zA-Z0-9_',
                u'已被占用']
        domain = self.get_argument("domain").strip()
        if len(domain) == 0:
            errors = errors + 1
            domain_error = 1
        else:
            if len(domain) > 16:
                errors = errors + 1
                domain_error = 2
            else:
                if len(domain) < 2:
                    errors = errors + 1
                    domain_error = 3
                else:
                    p = re.compile(r"([a-zA-Z0-9_])+", re.IGNORECASE)
                    if not p.search(domain):
                        errors = errors + 1
                        domain_error = 4
                    else:
                        domain_id = self.db.get("select id from fd_People where domain = %s", domain)
                        if domain_id:
                            errors = errors + 1
                            domain_error = 5 
        template_values['domain'] = domain
        template_values['domain_error'] = domain_error
        template_values['domain_error_message'] = domain_error_messages[domain_error]

        template_values['errors'] = errors
        if errors != 0:
            return self.render("signup.html", template_values=template_values)

        coltypelist = ['bk','ss','bs', 'zx']
        if coltype in coltypelist:
            college_type = coltypelist.index(coltype) + 1

        hashed = encrypt_password(password).encode('hex')

        signup_ip = self.request.remote_ip
        login_ip = signup_ip
        signup_date = time.strftime('%y-%m-%d %H:%M', time.localtime())
        login_date = signup_date
        uuid_ = binascii.b2a_hex(uuid.uuid4().bytes)
        if not (signup_ip and signup_date and uuid_):
            raise tornado.web.HTTPError(404)

        if coltype == 'zx':
            user_id = self.db.execute(
                    "INSERT INTO fd_People (email,name,password,zx_school,"
                    "zx_province_id,zx_city,college_type,domain,"
                    "signup_ip,login_ip,signup_date,login_date,uuid_) VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",email, username, hashed, college,
                    province_id['id'], city, college_type, domain, 
                    signup_ip, login_ip, signup_date, login_date, uuid_)

        if coltype == 'bk':
            city_id = self.db.get("select city_id from fd_College where id = %s", college_id['id'])
            if city_id:
                city_id = city_id['city_id']
            major_id = self.db.get("select id from fd_Major where name = %s", major)
            if major_id:
                major_id = major_id['id']
            else:
                major_id = self.db.execute("insert into fd_Major (name) values (%s)", major)
            user_id = self.db.execute(
                    "INSERT INTO fd_People (email,name,password,college_id,"
                    "city_id,major_id,college_type,domain,signup_ip,login_ip,"
                    "signup_date,login_date,uuid_) VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",email, username,
                    hashed, college_id['id'], city_id, major_id, college_type, 
                    domain, signup_ip, login_ip, signup_date, login_date, uuid_)

        if coltype == 'ss':
            ss_id = self.db.get("select id,city_id from fd_College where name = %s", template_values['sssscollege'])
            if ss_id:
                ss_college_id = ss_id['id']
                ss_city_id = ss_id['city_id']
            ss_major_id = self.db.get("select id from fd_Major where name = %s", template_values['ssssmajor'])
            if ss_major_id:
                ss_major_id = ss_major_id['id']
            else:
                ss_major_id = self.db.execute("insert into fd_Major (name) values (%s)", template_values['ssssmajor'])
            bk_id = self.db.get("select id,city_id from fd_College where name = %s", template_values['ssbkcollege'])
            if bk_id:
                bk_college_id = bk_id['id']
                bk_city_id = bk_id['city_id']
            bk_major_id = self.db.get("select id from fd_Major where name = %s", template_values['ssbkmajor'])
            if bk_major_id:
                bk_major_id = bk_major_id['id']
            else:
                bk_major_id = self.db.execute("insert into fd_Major (name) values (%s)", template_values['ssbkmajor'])
            user_id = self.db.execute(
                    "INSERT INTO fd_People (email,name,password,ss_college_id,ss_city_id,"
                    "ss_major_id,college_id,city_id,major_id,college_type,domain,signup_ip," 
                    "login_ip,signup_date,login_date,uuid_) VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",email, username, 
                    hashed, ss_college_id, ss_city_id, ss_major_id, bk_college_id, bk_city_id,bk_major_id, 
                    college_type, domain, signup_ip, login_ip, signup_date, login_date, uuid_)

        if coltype == 'bs':
            bs_id = self.db.get("select id,city_id from fd_College where name = %s", template_values['bsbscollege'])
            if bs_id:
                bs_college_id = bs_id['id']
                bs_city_id = bs_id['city_id']
            bs_major_id = self.db.get("select id from fd_Major where name = %s", template_values['bsbsmajor'])
            if bs_major_id:
                bs_major_id = bs_major_id['id']
            else:
                bs_major_id = self.db.execute("insert into fd_Major (name) values (%s)", template_values['bsbsmajor'])
            ss_id = self.db.get("select id,city_id from fd_College where name = %s", template_values['bssscollege'])
            if ss_id:
                ss_college_id = ss_id['id']
                ss_city_id = ss_id['city_id']
            ss_major_id = self.db.get("select id from fd_Major where name = %s", template_values['bsssmajor'])
            if ss_major_id:
                ss_major_id = ss_major_id['id']
            else:
                ss_major_id = self.db.execute("insert into fd_Major (name) values (%s)", template_values['bsssmajor'])
            bk_id = self.db.get("select id,city_id from fd_College where name = %s", template_values['bsbkcollege'])
            if bk_id:
                bk_college_id = bk_id['id']
                bk_city_id = bk_id['city_id']
            bk_major_id = self.db.get("select id from fd_Major where name = %s", template_values['bsbkmajor'])
            if bk_major_id:
                bk_major_id = bk_major_id['id']
            else:
                bk_major_id = self.db.execute("insert into fd_Major (name) values (%s)", template_values['bsbkmajor'])
            user_id = self.db.execute(
                    "INSERT INTO fd_People (email,name,password,bs_college_id,bs_city_id,bs_major_id,ss_college_id,"
                    "ss_city_id,ss_major_id,college_id,city_id,major_id,college_type,domain,signup_ip,login_ip,"
                    "signup_date,login_date,uuid_) VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",email, username, hashed, 
                    bs_college_id, bs_city_id, bs_major_id, ss_college_id, ss_city_id, ss_major_id, bk_college_id, 
                    bk_city_id, bk_major_id, college_type, domain, signup_ip, login_ip, signup_date, login_date, uuid_)

        self.set_secure_cookie("user", str(user_id))
        self.redirect("people/" + domain)

class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            return self.redirect("/")
        template_values = {}
        template_values['next'] = self.get_argument("next", '/')
        self.render("login.html", template_values=template_values)
    def post(self):
        errors = 0
        username_error = 0
        password_error = 0
        template_values = {}
        template_values['next'] = self.get_argument("next", '/')
        username = self.get_argument("username")
        password = self.get_argument("password")
        template_values['username'] = username
        people = self.db.get("SELECT * FROM fd_People WHERE name = %s", username)
        if not people:
            template_values['username_error'] = 1
            template_values['username_error_message'] = "用户名不存在"
            errors = errors + 1
        else:
            if not validate_password(str(people['password']).decode('hex'), password):
                template_values['password_error'] = 1
                template_values['password_error_message'] = "用户名与密码不匹配"
                errors = errors + 1
        if errors:
            return self.render("login.html", template_values=template_values)
        else:
            login_ip = self.request.remote_ip
            login_date = time.strftime('%y-%m-%d %H:%M', time.localtime())
            self.db.execute(
                    "UPDATE fd_People SET login_ip = %s, login_date = %s WHERE id = %s", login_ip, login_date, people['id'])
            self.set_secure_cookie("user", str(people['id']))
            next_url = self.get_argument("next", "/")
            self.redirect(next_url)

class ContactHandler(BaseHandler):
    def get(self):
        self.render("contact.html", template_values={})
    def post(self):
        username = self.get_argument("username", None)
        email = self.get_argument("email", None)
        subject = self.get_argument("subject", None)
        comments = self.get_argument("comment", None)
        ip = self.request.remote_ip
        user_agent = self.request.headers.get("User-Agent")
        nowtime = time.strftime('%y-%m-%d %H:%M', time.localtime())
        is_login = 1 if self.current_user else 0
        if not username or not email or not subject or not comments:
            raise tornado.web.HTTPError(404)
        else:
            contact_id = self.db.execute(
                    "INSERT INTO fd_Feedback (username,email,subject,comments,"
                    "ip,ua,date,is_login) VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s)",username, email, subject,
                    comments, ip, user_agent, nowtime, is_login)
            if not contact_id:
                raise tornado.web.HTTPError(404)
            else:
                self.write("right")

class AboutHandler(BaseHandler):
    def get(self):
        self.render("about.html")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("_xsrf")
        self.redirect(self.get_argument("next", "/"))

class PeopleHandler(BaseHandler):
    def get(self, domain):
        people = self.db.get("SELECT * FROM fd_People WHERE domain = %s", domain) 
        if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        if not self.current_user or self.current_user and self.current_user.id != people.id:
            template_values['is_self'] = False
        else:
            template_values['is_self'] = True
        template_values['id'] = people.id
        template_values['username'] = people.name
        template_values['domain'] = people.domain
        template_values['uuid'] = people.uuid_
        template_values['has_selfdesc'] = people.has_selfdesc
        college_type = people.college_type
        template_values['college_type'] = college_type
        if college_type == 1:
            city = self.db.get("select name from fd_City where id = %s", people.city_id)
            template_values['city_id'] = people.city_id
            template_values['city'] = city.name 
            college = self.db.get("select name from fd_College where id = %s", people.college_id)
            template_values['college_id'] = people.college_id
            template_values['college'] = college.name 
            major = self.db.get("select name from fd_Major where id = %s", people.major_id)
            template_values['major_id'] = people.major_id
            template_values['major'] = major.name 
        if college_type == 2:
            cities = self.db.query("select name from fd_City where id in (%s,%s) order by find_in_set(id, '%s,%s')", people.city_id, people.ss_city_id, people.city_id, people.ss_city_id)
            template_values['city_id'] = people.city_id
            template_values['city'] = cities[0].name
            template_values['ss_city_id'] = people.ss_city_id
            template_values['ss_city'] = cities[len(cities)-1].name 

            colleges = self.db.query("select name from fd_College where id in (%s,%s) order by find_in_set(id, '%s,%s')", people.college_id, people.ss_college_id, people.college_id, people.ss_college_id)
            template_values['college_id'] = people.college_id
            template_values['college'] = colleges[0].name
            template_values['ss_college_id'] = people.ss_college_id
            template_values['ss_college'] = colleges[len(colleges)-1].name 

            majors = self.db.query("select name from fd_Major where id in (%s,%s) order by find_in_set(id, '%s,%s')", people.major_id, people.ss_major_id, people.major_id, people.ss_major_id)
            template_values['major_id'] = people.major_id
            template_values['major'] = majors[0].name
            template_values['ss_major_id'] = people.ss_major_id
            template_values['ss_major'] = majors[len(majors)-1].name 

        if college_type == 3:
            cities = self.db.query("select name from fd_City where id in (%s,%s,%s) order by find_in_set(id, '%s,%s,%s')", people.city_id, people.ss_city_id, people.bs_city_id, people.city_id, people.ss_city_id, people.bs_city_id)
            template_values['city_id'] = people.city_id
            template_values['city'] = cities[0].name
            template_values['ss_city_id'] = people.ss_city_id
            template_values['ss_city'] = cities[len(cities)-1 if len(cities)==2 and people.bs_city_id==people.ss_city_id else len(cities)-2].name 
            template_values['bs_city_id'] = people.bs_city_id
            template_values['bs_city'] = cities[len(cities)-1].name 

            colleges = self.db.query("select name from fd_College where id in (%s,%s,%s) order by find_in_set(id, '%s,%s,%s')", people.college_id, people.ss_college_id, people.bs_college_id, people.college_id, people.ss_college_id, people.bs_college_id)
            template_values['college_id'] = people.college_id
            template_values['college'] = colleges[0].name
            template_values['ss_college_id'] = people.ss_college_id
            template_values['ss_college'] = colleges[len(colleges)-1 if len(colleges)==2 and people.bs_college_id==people.ss_college_id else len(colleges)-2].name 
            template_values['bs_college_id'] = people.bs_college_id
            template_values['bs_college'] = colleges[len(colleges)-1].name 

            majors = self.db.query("select name from fd_Major where id in (%s,%s,%s) order by find_in_set(id, '%s,%s,%s')", people.major_id, people.ss_major_id, people.bs_major_id, people.major_id, people.ss_major_id, people.bs_major_id)
            template_values['major_id'] = people.major_id
            template_values['major'] = majors[0].name
            template_values['ss_major_id'] = people.ss_major_id
            template_values['ss_major'] = majors[len(majors)-1 if len(majors)==2 and people.bs_major_id==people.ss_major_id else len(majors)-2].name 
            template_values['bs_major_id'] = people.bs_major_id
            template_values['bs_major'] = majors[len(majors)-1].name 
        if college_type == 4:
            template_values['zx_city'] = people.zx_city
            template_values['zx_school'] = people.zx_school
            zx_province = self.db.get("select name from fd_Province where id = %s", people.zx_province_id)
            template_values['zx_province'] = zx_province.name

        template_values['follow_count'] = self.ufg.follow_count(people.id)
        template_values['follower_count'] = self.ufg.follower_count(people.id)
        template_values['is_follow'] = self.ufg.is_follow(self.current_user.id, people.id) if self.current_user else False
        template_values['image'] = self.static_url("img/no_avatar.jpg")
        template_values['selfdesc'] = ""
        if template_values['has_selfdesc']:
            selfdesc = self.db.get("select selfdesc from fd_Selfdesc where user_id = %s", 
                    template_values['id'])
            if not selfdesc: raise tornado.web.HTTPError(405)
            template_values['selfdesc'] = self.br(selfdesc.selfdesc).strip()
        isself = template_values['id'] == self.current_user.id if self.current_user else False
        template_values['activities'] = self.uag.get_top_activities(template_values['id'], self.db, isself) 
        template_values['activity_count'] = self.uag.count_activity(template_values['id']) 
        template_values['statuses'] = self.uag.get_top_sub_activities(template_values['id'], 1, isself) 
        template_values['status_count'] = self.uag.count_sub_activity(template_values['id'], 1) 
        template_values['notes'] = self.uag.get_top_sub_activities(template_values['id'], 2, isself) 
        template_values['note_count'] = self.uag.count_sub_activity(template_values['id'], 2) 
        template_values['links'] = self.uag.get_top_sub_activities(template_values['id'], 3, isself) 
        template_values['link_count'] = self.uag.count_sub_activity(template_values['id'], 3) 
        template_values['docs'] = self.uag.get_top_sub_activities(template_values['id'], 4, isself) 
        template_values['doc_count'] = self.uag.count_sub_activity(template_values['id'], 4) 
        self.render("people.html", template_values=template_values)

class FollowingHandler(FollowBaseHandler):
    def get(self, domain):
        template_values = self.follow(domain, 'following')
        self.render("follow.html", template_values=template_values)

class FollowerHandler(FollowBaseHandler):
    def get(self, domain):
        template_values = self.follow(domain, 'follower')
        self.render("follow.html", template_values=template_values)

class RegionHandler(BaseHandler):
    def get(self, region, name):
        if region == "college":
            region_get = self.db.get("SELECT id,image_path FROM fd_College where name = %s", name)
        elif region == "city":
            region_get = self.db.get("SELECT id FROM fd_City where name = %s", name)
        elif region == "major":
            region_get = self.db.get("SELECT id FROM fd_Major where name = %s", name)
        if not region_get: raise tornado.web.HTTPError(404)
        region_id = region_get.id
        if region == "city": 
            people = self.db.query("SELECT id,name,domain,uuid_ FROM fd_People WHERE (city_id=%s and college_type=1) or (ss_city_id=%s and college_type=2) or (bs_city_id=%s and college_type=3)", region_id, region_id, region_id) 
        elif region == "college":
            image_path = region_get.image_path
            people = self.db.query("SELECT id,name,domain,uuid_ FROM fd_People WHERE (college_id=%s and college_type=1) or (ss_college_id=%s and college_type=2) or (bs_college_id=%s and college_type=3)", region_id, region_id, region_id) 
        elif region == "major":
            people = self.db.query("SELECT id,name,domain,uuid_ FROM fd_People WHERE (major_id=%s and college_type=1) or (ss_major_id=%s and college_type=2) or (bs_major_id=%s and college_type=3)", region_id, region_id, region_id) 
        template_values = {}
        template_values['region_id'] = region_id
        template_values['region'] = name
        template_values['type'] = region
        template_values['image'] = self.static_url("img/no_photo.gif")
        if region == "college" and image_path:
            template_values['image'] = self.static_url("schoolimage/" + image_path)
        for i in range(len(people)):
            people[i].is_follow = self.ufg.is_follow(self.current_user.id, people[i].id) if self.current_user else False
            people[i].image = self.avatar("m", people[i].id, people[i].uuid_)
            if not self.current_user or self.current_user and self.current_user.id != people[i].id:
                people[i].is_self = False 
            else:
                people[i].is_self = True
        template_values['people'] = people 
        self.render("region.html", template_values=template_values)

class ExistHandler(BaseHandler):
    def post(self):
        prop = self.get_argument("property",None)
        proptype = self.get_argument("propertype",None)
        if proptype == "username":
            user_id = get_id_by_name(self.db, self.rd, prop)
            if user_id:
                self.write("已被占用")
            else: 
                self.write("可以使用")
        if proptype == "email":
            user_id = self.db.get("select id from fd_People where email = %s", prop)
            if user_id:
                self.write("该邮箱已被人注册")
            else: 
                self.write("可以使用")
        if proptype == "domain":
            user_id = self.db.get("select id from fd_People where domain = %s", prop)
            if user_id:
                self.write("已被占用")
            else: 
                self.write("可以使用")
        if proptype == "college":
            college_id = self.db.get("select id from fd_College where name = %s", prop)
            if college_id:
                self.write("可以注册")
            else: 
                self.write("学校不存在或不是全称")

class FollowHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        from_user = self.get_argument("from_user",None)
        to_user = self.get_argument("to_user",None)
        if from_user == to_user or from_user == 0 or to_user == 0: raise tornado.web.HTTPError(405)
        if self.ufg.follow(from_user, to_user):
            acttime = time.strftime('%y-%m-%d %H:%M', time.localtime())
            redacttime = acttime[4:] if acttime[3] == '0' else acttime[3:]
            actto = self.db.get("select name from fd_People where id = %s", to_user).name
            actdict = {'time':redacttime}
            add_activity(self.rd, from_user, to_user, 0, actdict)
        else:
            self.write('already')

class UnfollowHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        from_user = self.get_argument("from_user",None)
        to_user = self.get_argument("to_user",None)
        if from_user == to_user or from_user == 0 or to_user == 0: raise tornado.web.HTTPError(405)
        if self.ufg.unfollow(from_user, to_user):
            #actto = self.db.get("select name from fd_People where id = %s", to_user).name
            del_activity(self.rd, from_user, 0, to_user)
        else:
            self.write('already')

class SelfdescHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        selfdesc = self.get_argument("selfdesc",None)
        if not selfdesc: raise tornado.web.HTTPError(405)
        if self.current_user.has_selfdesc:
            self.db.execute("update fd_Selfdesc set selfdesc = %s"
                    "where user_id = %s", selfdesc, self.current_user.id)
        else:
            selfdesc_id = self.db.execute("insert into fd_Selfdesc (user_id, selfdesc)"
                    " values (%s,%s)", self.current_user.id, selfdesc)
            if selfdesc_id:
                self.db.execute("update fd_People set has_selfdesc"
                        " = 1 where id = %s", self.current_user.id)
        self.write(self.br(selfdesc).strip())

class PubstatusHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        status = self.get_argument("statustext",None)
        if not status: raise tornado.web.HTTPError(405)
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
        user_id = self.current_user.id
        status_id = self.db.execute("insert into fd_Status (user_id, "
                    " status, pubdate) values (%s,%s,%s)", user_id, 
                    status, pubdate)
        #redis
        if status_id:
            actdict = {'time':redpubdate, 'status':status}
            addresult = add_activity(self.rd, user_id, status_id, 1, actdict)
            if addresult:
                self.write(''.join([encode(str(status_id)), ',', self.avatar('m',self.current_user.id,self.current_user.uuid_),',', self.br(self.at(linkify(status, extra_params="target='_blank' rel='nofollow'")))]))
            else:
                self.write("Something wrong...")

class DeleteActivityHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        user = self.get_argument("user",None)
        actto = self.get_argument("actto",None)
        acttype = self.get_argument("acttype",None)
        user_id = get_id_by_name(self.db, self.rd, user)
        if len(actto) < 8 or not user_id or int(user_id) != self.current_user.id:
            raise tornado.web.HTTPError(405)
        acttype = int(acttype)
        actto = decode(actto)
        # don't remove in db now because data is not got wholy in redis,just mark it
        if acttype == 1:
            self.db.execute("update fd_Status set status_ = 1 where id = %s", actto)
        elif acttype == 2:
            self.db.execute("update fd_Note set status_ = 2 where id = %s", actto)
        elif acttype == 3:
            self.db.execute("update fd_Link set status_ = 2 where id = %s", actto)
        elif acttype == 4:
            doc_id = self.db.get("select doc_id,name,user_id from fd_Doc where id = %s", actto)
            if not doc_id:
                raise tornado.web.HTTPError(500)
            tld = doc_id.name.split(".").pop()
            prepath = "/data/static/usrdoc/%s/%s.%s" % (doc_id.user_id, doc_id.doc_id, tld)
            jpgpath = "/work/Dormforge/static/usrdoc/%s/%s.jpg" % (doc_id.user_id, doc_id.doc_id)
            swfpath = "/work/Dormforge/static/usrdoc/%s/%s.swf" % (doc_id.user_id, doc_id.doc_id)
            if os.path.exists(prepath) and os.path.exists(jpgpath) and os.path.exists(swfpath):
                os.remove(prepath)
                os.remove(jpgpath)
                os.remove(swfpath)
                self.db.execute("update fd_Doc set status_ = 2 where id = %s", actto)
        del_activity(self.rd, user_id, acttype, actto)

class StatusHandler(BaseHandler):
    def get(self, status_id):
        template_values = {}
        if len(status_id) < 8:
            raise tornado.web.HTTPError(404)
        status_id = decode(status_id)
        status = self.db.get("select p.name,p.domain,p.uuid_,p.id,s.status,s.pubdate,s.status_ "
                "from fd_People p, fd_Status s where s.user_id = p.id and "
                "s.id = %s", status_id)
        if not status or status.status_ == 1:
            raise tornado.web.HTTPError(404)
        template_values['activity'] = status
        comments = self.db.query("select p.name,p.domain,p.uuid_,p.id,c.comments, "
                "c.pubdate from fd_People p, fd_Stacomm c where p.id"
                "=c.user_id and status_id = %s", status_id)
        template_values['comments_length'] = len(comments)
        template_values['comments'] = comments
        self.render("status.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self, status_id):
        if len(status_id) < 8:
            raise tornado.web.HTTPError(404)
        status_id = decode(status_id)
        comments = self.get_argument("commenttext",None)
        user_id = self.current_user.id
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        comment_id = self.db.execute("insert into fd_Stacomm (user_id, "
                    " status_id, comments, pubdate) values (%s,%s,%s,%s)", 
                    user_id, status_id, comments, pubdate)
        if comment_id:
            status_key = self.rd.keys('status*%s' % status_id)[0]
            prev_comments_num = self.rd.hget(status_key, 'comm')
            if not prev_comments_num:
                comments_num = 1
            else:
                comments_num = int(prev_comments_num) + 1
            self.rd.hset(status_key, 'comm', comments_num)
            self.write(''.join([self.avatar('m',self.current_user.id,self.current_user.uuid_), ',', self.br(self.at(linkify(comments, extra_params="target='_blank' rel='nofollow'")))]))

class LinkHandler(BaseHandler):
    def get(self, link_id):
        template_values = {}
        if len(link_id) < 8:
            raise tornado.web.HTTPError(404)
        link_id = decode(link_id)
        link = self.db.get("select p.name,p.domain,p.uuid_,p.id,l.url,l.title,"
                "l.summary,l.pubdate,l.status_ "
                "from fd_People p, fd_Link l where l.user_id = p.id and "
                "l.id = %s", link_id)
        if not link or link.status_ == 1 and link.name != self.current_user.name:
            raise tornado.web.HTTPError(404)
        template_values['activity'] = link
        comments = self.db.query("select p.name,p.domain,p.uuid_,p.id,c.comments, "
                "c.pubdate from fd_People p, fd_Linkcomm c where p.id"
                "=c.user_id and link_id = %s", link_id)
        template_values['comments_length'] = len(comments)
        template_values['comments'] = comments
        self.render("link.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self, link_id):
        if len(link_id) < 8:
            raise tornado.web.HTTPError(404)
        link_id = decode(link_id)
        comments = self.get_argument("commenttext",None)
        user_id = self.current_user.id
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        comment_id = self.db.execute("insert into fd_Linkcomm (user_id, "
                    " link_id, comments, pubdate) values (%s,%s,%s,%s)", 
                    user_id, link_id, comments, pubdate)
        if comment_id:
            link_key = self.rd.keys('link*%s' % link_id)[0]
            prev_comments_num = self.rd.hget(link_key, 'comm')
            if not prev_comments_num:
                comments_num = 1
            else:
                comments_num = int(prev_comments_num) + 1
            self.rd.hset(link_key, 'comm', comments_num)
            self.write(''.join([self.avatar('m',self.current_user.id,self.current_user.uuid_), ',', self.br(self.at(linkify(comments, extra_params="target='_blank' rel='nofollow'")))]))

class PubnoteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        template_values = {}
        noteid = self.get_argument("id",None)
        if noteid:
            if len(noteid) < 8:
                raise tornado.web.HTTPError(404)
            note_id = decode(noteid)
            note = self.db.get("select id,title,note,user_id,status_ "
                    "from fd_Note where id = %s", note_id)
            if not note or note.user_id != self.current_user.id:
                raise tornado.web.HTTPError(404)
            note.id = noteid
            template_values['note'] = note
        self.render("pubnote.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self):
        noteid = self.get_argument("id",None)
        notetype = self.get_argument("notetype",None)
        notetitle = self.get_argument("notetitle",None)
        notecontent = self.get_argument("notecontent",None)
        #status_:{0:public,1:private,2:delted
        rednotecontent = notecontent
        if len(notecontent) > 150:
            rednotecontent = notecontent[:140] + " ..."
        status_ = int(notetype)
        user_id = self.current_user.id
        if noteid:
            noteid = decode(noteid)
            note_user = self.db.get("select user_id from fd_Note where id = %s", noteid)
            if not note_user or note_user.user_id != user_id:
                raise tornado.web.HTTPError(404)
            self.db.execute("update fd_Note set title = %s, note = %s,"
                    "status_ = %s where id = %s", notetitle, notecontent, status_, noteid)
            note_key = "note:%s:%s" % (user_id, noteid)
            actdict = {'title':notetitle, 'content':rednotecontent, 'status':status_}
            if self.rd.hmset(note_key, actdict):
                self.write("right")
            else:
                self.write("wrong")
        else:
            pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
            redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
            note_id = self.db.execute("insert into fd_Note (user_id, title, "
                    "note, pubdate, status_) values (%s,%s,%s,%s,%s)", user_id,
                    notetitle, notecontent, pubdate, status_)
            if note_id:
                actdict = {'time':redpubdate, 'title':notetitle, 
                        'content':rednotecontent, 'status':status_}
                addresult = add_activity(self.rd, user_id, note_id, 2, actdict)
                if addresult:
                    self.write(encode(str(note_id)))
                    #self.write("right")
                else:
                    self.write("wrong")

class ViewnoteHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        noteid = self.get_argument("note_id",None)
        if not noteid or len(noteid) < 8:
            raise tornado.web.HTTPError(404)
        noteid = decode(noteid)
        note = self.db.get("select note from fd_Note where "
                "id = %s", noteid)
        if note:
            self.write(self.br(self.at(linkify(note.note, extra_params="target='_blank' rel='nofollow'"))))
        else:
            self.write("wrong")

class NoteHandler(BaseHandler):
    def get(self, note_id):
        template_values = {}
        if len(note_id) < 8:
            raise tornado.web.HTTPError(404)
        note_id = decode(note_id)
        note = self.db.get("select p.name,p.domain,n.title,n.note,n.status_ "
                ",n.pubdate from fd_People p, fd_Note n where n.user_id = p.id and "
                "n.id = %s", note_id)
        if not note or note.status_ == 2 or \
        note.status_ == 1 and note.name != self.current_user.name:
            raise tornado.web.HTTPError(404)
        template_values['activity'] = note
        comments = self.db.query("select p.name,p.domain,p.uuid_,p.id,c.comments, "
                "c.pubdate from fd_People p, fd_Notecomm c where p.id"
                "=c.user_id and note_id = %s", note_id)
        template_values['comments_length'] = len(comments)
        template_values['comments'] = comments
        self.render("note.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self, note_id):
        if len(note_id) < 8:
            raise tornado.web.HTTPError(404)
        note_id = decode(note_id)
        comments = self.get_argument("commenttext",None)
        user_id = self.current_user.id
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        comment_id = self.db.execute("insert into fd_Notecomm (user_id, "
                    " note_id, comments, pubdate) values (%s,%s,%s,%s)", 
                    user_id, note_id, comments, pubdate)
        if comment_id:
            note_key = self.rd.keys('note*%s' % note_id)[0]
            prev_comments_num = self.rd.hget(note_key, 'comm')
            if not prev_comments_num:
                comments_num = 1
            else:
                comments_num = int(prev_comments_num) + 1
            self.rd.hset(note_key, 'comm', comments_num)
            self.write(''.join([self.avatar('m',self.current_user.id,self.current_user.uuid_), ',', self.br(self.at(linkify(comments, extra_params="target='_blank' rel='nofollow'")))]))

class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, setting):
        template_values = {}
        template_values['setting'] = setting
        if setting == 'account':
            page_title = '账户设置'
            template_values['username'] = self.current_user.name
            template_values['domain'] = self.current_user.domain
            template_values['username_error'] = 0
            template_values['domain_error'] = 0
        elif setting == 'avatar':
            page_title = '头像设置'
            template_values['id'] = self.current_user.id
            template_values['uuid'] = self.current_user.uuid_
        elif setting == 'passwd':
            page_title = '修改密码'
        elif setting == 'delete':
            page_title = '删除账户'
        else: 
            page_title = '18周'
        template_values['page_title'] = page_title
        template_values['errors'] = 0
        self.render("settings.html", template_values=template_values)

    @tornado.web.authenticated
    def post(self, setting):
        template_values = {}
        errors = 0
        username_error = 0
        domain_error = 0
        template_values['setting'] = setting
        if setting == 'account':
            page_title = '账户设置'
            username_error = 0
            username_error_messages = ['',
                    u'一个月之内只能修改一次用户名',
                    u'请输入用户名',
                    u'用户名不能超过16个字符',
                    u'用户名不能少于2个字符',
                    u'该用户名已被占用',
                    ]
            username = self.get_argument("name", None)
            lastuc = self.db.get("select chtimedelta from fd_Change where user_id = %s and chtype = 1", self.current_user.id)
            if lastuc:
                lastdelta = lastuc.chtimedelta
                timedelta = lastdelta - int(time.time())
                if username != self.current_user.name and timedelta < 2592000: #24*60*60*30
                    errors = errors + 1
                    username_error = 1
            if username_error != 1:
                if len(username) == 0:
                    errors = errors + 1
                    username_error = 2
                elif len(username) > 16:
                    errors = errors + 1
                    username_error = 3
                elif len(username) < 2:
                    errors = errors + 1
                    username_error = 4
                else:
                    if username != self.current_user.name:
                        user_id = get_id_by_name(self.db, self.rd, username)
                        if user_id:
                            errors = errors + 1
                            username_error = 5
                        else:
                            self.rd.delete("u:name:%s" % self.current_user.name)
                            self.rd.delete("u:%s" % self.current_user.id)
                            self.db.execute("update fd_People set name = %s where id = %s", username, self.current_user.id)
                            pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
                            pubdelta = int(time.time())
                            if lastuc:
                                self.db.execute("update fd_Change set chtime = %s,chtimedelta = %s where user_id = %s and chtype = %s", pubdate, pubdelta, self.current_user.id, 1)
                            else:
                                self.db.execute("insert into fd_Change set chtime = %s, chtimedelta = %s, user_id = %s, chtype = %s", pubdate, pubdelta, self.current_user.id, 1)
                            self.current_user.name = username
            domain_error_messages = ['',
                    u'一个月之内只能修改一次个性域名',
                    u'请输入个性域名',
                    u'个性域名不能超过16个字符',
                    u'个性域名不能少于2个字符',
                    u'个性域名不符合规则，请使用a-zA-Z0-9_',
                    u'该个性域名已被占用']
            domain = self.get_argument("domain", None)
            lastdc = self.db.get("select chtimedelta from fd_Change where user_id = %s and chtype = 2", self.current_user.id)
            if lastdc:
                lastdelta = lastdc.chtimedelta
                timedelta = lastdelta - int(time.time())
                if domain != self.current_user.domain and timedelta < 2592000: #24*60*60*30
                    errors = errors + 1
                    domain_error = 1
            if domain_error != 1:
                if len(domain) == 0:
                    errors = errors + 1
                    domain_error = 2
                elif len(domain) > 16:
                    errors = errors + 1
                    domain_error = 3
                elif len(domain) < 2:
                    errors = errors + 1
                    domain_error = 4
                else:
                    if domain != self.current_user.domain:
                        p = re.compile(r"([a-zA-Z0-9_])+", re.IGNORECASE)
                        if not p.search(domain):
                            errors = errors + 1
                            domain_error = 5
                        else:
                            domain_id = self.db.get("select id from fd_People where domain = %s", domain)
                            if domain_id:
                                errors = errors + 1
                                domain_error = 6
                            else:
                                self.db.execute("update fd_People set domain = %s where id = %s", domain, self.current_user.id)
                                pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
                                pubdelta = int(time.time())
                                if lastdc:
                                    self.db.execute("update fd_Change set chtime = %s,chtimedelta = %s where user_id = %s and chtype = %s", pubdate, pubdelta, self.current_user.id, 2)
                                else:
                                    self.db.execute("insert into fd_Change set chtime = %s, chtimedelta = %s, user_id = %s, chtype = %s", pubdate, pubdelta, self.current_user.id, 2)
                                self.current_user.domain = domain
            template_values['username'] = self.current_user.name
            template_values['domain'] = self.current_user.domain
            template_values['username_error'] = username_error
            template_values['domain_error'] = domain_error
            if username_error:
                template_values['newname'] = username
                template_values['username_error_message'] = username_error_messages[username_error]
            if domain_error:
                template_values['newdomain'] = domain
                template_values['domain_error_message'] = domain_error_messages[domain_error]
        elif setting == 'avatar':
            page_title = '头像设置'
            avatar_error = 0
            avatar_error_messages = ['',
                    u'请选择图片',
                    u'图片格式不正确',
                    u'图片不能大于2MB',
                    ]
            if not self.request.files:
                errors = errors + 1
                avatar_error = 1
            else:
                f = self.request.files['avatar'][0]
                if f['filename'].split(".").pop().lower() not in ["jpg", "png", "gif", "jpeg"]:
                    errors = errors + 1
                    avatar_error = 2
                else:
                    if len(f['body']) > 1024*1024*2:
                        errors = errors + 1
                        avatar_error = 3
                    else:
                        picsize = ["s", "m", "l", "xl"]
                        picsizedict = {"xl":150,"l":100,"m":50,"s":25}
                        rawname = f['filename']
                        tempdstname = ''.join([str(int(time.time())), '.', rawname.split('.').pop()])
                        dstname = ''.join([self.current_user.uuid_, '.jpg'])
                        shard = str(self.current_user.id % 40)
                        thbname = "thumb_" + tempdstname
                        tf = tempfile.NamedTemporaryFile()
                        tf.write(f['body'])
                        tf.seek(0)
                        for ps in picsize:
                            img = Image.open(tf.name)
                            imgsize = picsizedict[ps]
                            img.thumbnail((imgsize,imgsize),resample=1)
                            imgpath = "/work/Dormforge/static/usrimg/%s" % shard
                            img = img.convert("RGB")
                            try:
                                img.save("%s/%s_%s" % (imgpath, ps, dstname))
                            except IOError:
                                os.makedirs(imgpath)
                                img.save("%s/%s_%s" % (imgpath, ps, dstname))
                        tf.close()
            if errors != 0:
                template_values['errors'] = errors
                template_values['avatar_error'] = avatar_error
                template_values['avatar_error_message'] = avatar_error_messages[avatar_error]
                template_values['page_title'] = page_title
                template_values['id'] = self.current_user.id
                template_values['uuid'] = self.current_user.uuid_
                return self.render("settings.html", template_values=template_values)
        elif setting == 'passwd':
            page_title = '修改密码'
            #password verify
            password_error = 0
            password_error_messages = ['',
                u'请输入当前密码',
                u'请输入新密码',
                u'请输入新密码确认',
                u'密码长度不能超过 32 个字符',
                u'两次输入的密码不一致',
                u'当前密码不正确',
                ]
            old = self.get_argument("old", None)
            new = self.get_argument("new", None)
            confirm = self.get_argument("confirm", None)
            if not old or len(old) == 0:
                errors = errors + 1
                password_error = 1
            else:
                if not new or len(new) == 0:
                    errors = errors + 1
                    password_error = 2
                else:
                    if not confirm or len(confirm) == 0:
                        errors = errors + 1
                        password_error = 3
                    else:
                        old = old.strip()
                        new = new.strip()
                        confirm = confirm.strip()
                        if len(confirm) > 32:
                            errors = errors + 1
                            password_error = 4
                        else:
                            if confirm != new:
                                errors = errors + 1
                                password_error = 5
                            else:
                                if not validate_password(self.current_user.password.decode('hex'), old):
                                    errors = errors + 1
                                    password_error = 6
            if errors != 0:
                template_values['old'] = old
                template_values['new'] = new
                template_values['confirm'] = confirm
                template_values['errors'] = errors
                template_values['password_error'] = password_error
                template_values['password_error_message'] = password_error_messages[password_error]
                template_values['page_title'] = page_title
                return self.render("settings.html", template_values=template_values)
            if new != old:
                hashed = encrypt_password(new).encode('hex')
                self.db.execute("update fd_People set password = %s where id = %s", hashed, self.current_user.id)
        template_values['errors'] = errors
        if errors == 0:
            template_values['success'] = 1
        template_values['page_title'] = page_title
        template_values['id'] = self.current_user.id
        template_values['uuid'] = self.current_user.uuid_
        return self.render("settings.html", template_values=template_values)

class SettingModule(tornado.web.UIModule):
    def render(self, template_values):
        return self.render_string("modules/%s.html" % template_values['setting'], template_values=template_values)

class EditlinkHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        template_values = {}
        pubtype = self.get_argument("pubtype",0)
        linkid = self.get_argument("id",None)
        if linkid and pubtype == 0:
            if len(linkid) < 8:
                raise tornado.web.HTTPError(404)
            link_id = decode(linkid)
            link = self.db.get("select url,title,summary,user_id,status_, "
                    "tags from fd_Link where id = %s", link_id)
            if not link or link.user_id != self.current_user.id:
                raise tornado.web.HTTPError(404)
            template_values['url'] = link.url
            template_values['title'] = link.title
            template_values['summary'] = link.summary
            template_values['tags'] = link.tags
            template_values['id'] = linkid
            template_values['checked'] = "checked" if link.status_ == 1 else ""
            pubtype = 2
        else:
            url = self.get_argument("url",None)
            title = self.get_argument("title",None)
            template_values['url'] = url
            template_values['title'] = title
        template_values['sugg'] = pubtype or self.current_user.sugg_link
        template_values['pubtype'] = pubtype
        self.render("editlink.html", template_values=template_values)

    @tornado.web.authenticated
    def post(self):
        url = self.get_argument("linkurl",None)
        title = self.get_argument("linktitle",None)
        summary = self.get_argument("linksummary",None)
        tag = self.get_argument("linktag",None)
        oldtag = self.get_argument("oldtag",None)
        linktype = self.get_argument("linktype",None)
        pubtype = self.get_argument("pubtype",0)
        linkid = self.get_argument("linkid",None)
        pubtype = int(pubtype)
        if linkid:
            linkid = decode(linkid)
            link_user = self.db.get("select user_id from fd_Link where id = %s", linkid)
            if not link_user or link_user.user_id != self.current_user.id:
                raise tornado.web.HTTPError(404)
        if not url:
            raise tornado.web.HTTPError(500)
        url = url[7:] if url.startswith("http://") else url
        url = url[8:] if url.startswith("https://") else url
        if linkid:
            link_sql = ["update fd_Link set url = '%s'," % url]
        else:
            link_sql = ["insert into fd_Link set url = '%s'," % url]
        if title:
            link_sql.append("title = '%s'," % title.replace("'", "''"))
        if summary:
            link_sql.append("summary = '%s'," % summary.replace("'", "''"))
        if tag:
            tag = tag.strip().replace(' ',',')
            tag = tag.strip().replace('，',',')
            tags = tag.split(",")
            taglists = []
            for t in tags:
                if t in taglists:
                    continue
                taglists.append(t)
            newtag = " ".join(taglists)
            if not (pubtype == 2 and newtag == oldtag):
                link_sql.append("tags = '%s'," % newtag.replace("'", "''"))
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
        if pubtype == 2:
            link_sql.append("status_ = %s where id = %s" % (linktype,linkid))
        else:
            link_sql.append("user_id = %s,pubdate = '%s',status_ = %s" % (self.current_user.id,pubdate,linktype))
        fd_link_sql = "".join(link_sql)
        link_id = self.db.execute(fd_link_sql)
        if tag:
            if pubtype != 2 or pubtype == 2 and newtag != oldtag:
                for t in taglists:
                    tag_id = self.db.get("select id from fd_Tag where tag = %s", t)
                    if tag_id:
                        tag_id = tag_id.id
                    else:
                        tag_id = self.db.execute("insert into fd_Tag (tag) values (%s)", t)
                    if linkid:
                        with_link_id = linkid
                    elif link_id:
                        with_link_id = link_id
                    ltag_id = self.db.execute("insert into fd_Ltag (link_id,tag_id) values (%s,%s)", with_link_id, tag_id)
        if linkid: 
            link_key = "link:%s:%s" % (self.current_user.id, linkid)
            actdict = {'url':url, 'status':linktype}
            if title:
                actdict['title'] = title
            if summary:
                actdict['summary'] = summary
            if self.rd.hmset(link_key, actdict):
                self.write("/")
        elif link_id:
            actdict = {'time':redpubdate, 'url':url, 'status':linktype}
            if title:
                actdict['title'] = title
            if summary:
                actdict['summary'] = summary
            addresult = add_activity(self.rd, self.current_user.id, link_id, 3, actdict)
            if addresult:
                self.write("http://" + url)

class PNFHandler(BaseHandler):
    def get(self):
        self.set_status(404)
        self.render("404.html")

class CansugHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        self.current_user.sugg_link = 1
        self.db.execute("update fd_People set sugg_link = 1 where id = %s", self.current_user.id)

class EditdocHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        template_values = {}
        doc_id = self.get_argument("id", None)
        if doc_id:
            if len(doc_id) < 8:
                raise tornado.web.HTTPError(404)
            docid = decode(doc_id)
            doc = self.db.get("select title,summary,tags,user_id,status_ "
                    "from fd_Doc where id = %s", docid)
            if not doc or doc.user_id != self.current_user.id:
                raise tornado.web.HTTPError(404)
            template_values['title'] = doc.title
            template_values['summary'] = doc.summary
            template_values['tag'] = doc.tags
            if doc.status_ == 1:
                template_values['checked'] = 'checked'
            template_values['id'] = doc_id
        self.render("editdoc.html", template_values=template_values)
        
    @tornado.web.authenticated
    def post(self):
        template_values = {}
        title = self.get_argument("title", None)
        summary = self.get_argument("summary", None)
        tag = self.get_argument("tag", None)
        secret = self.get_argument("secret", None)
        endocid = self.get_argument("docid", None)
        oldtag = self.get_argument("oldtag", None)
        errors = 0
        title_error = 0
        title_error_messages = ['',
                u'请输入标题',
                ]
        if not endocid:
            name = self.get_argument("doc.name", None)
            content_type = self.get_argument("doc.content_type", None)
            path = self.get_argument("doc.path", None)
            md5 = self.get_argument("doc.md5", None)
            size = self.get_argument("doc.size", None)
        if not title or len(title) == 0:
            errors = errors + 1
            title_error = 1
            template_values['title_error'] = title_error
            template_values['title_error_message'] = title_error_messages[title_error]
        else:
            doc_error = 0
            doc_error_messages = ['',
                    u'请选择文档',
                    u'暂时不支持该文档格式',
                    u'文档不能大于20M',
                    u"该文档已被上传过",
                    ]
            if not endocid:
                if not (name and path and md5 and size):
                    errors = errors + 1
                    doc_error = 1
                else:
                    if name.split(".").pop().lower() not in ["doc", "docx", "ppt", "pptx", "pdf", "xls"]:
                        os.remove(path)
                        errors = errors + 1
                        doc_error = 2
                    else:
                        if int(size) > 1024*1024*20:
                            os.remove(path)
                            errors = errors + 1
                            doc_error = 3
                        else:
                            predoc = self.db.get("select * from fd_Doc where md5 = %s and status_ = 0", md5)
                            if predoc:
                                os.remove(path)
                                errors = errors + 1
                                doc_error = 4
                            else:
                                usrpath = u"/data/static/usrdoc/%s/" % self.current_user.id
                                staticpath = u"/work/Dormforge/static/usrdoc/%s/" % self.current_user.id
                                if not os.path.exists(usrpath):
                                    os.makedirs(usrpath)
                                if not os.path.exists(staticpath):
                                    os.makedirs(staticpath)
                                docid = "".join([path.split("/").pop(), str(time.time()).split(".")[0]])
                                doctype = name.split(".").pop().lower()
                                usrdoc = ''.join([usrpath, docid, '.', doctype])
                                shutil.move(path, usrdoc)
                                if name.split(".").pop().lower() != 'pdf':
                                    usrpdf = ''.join([usrpath, docid, ".pdf"])
                                    usrjpg = ''.join([staticpath, docid, ".jpg"])
                                    usrswf = ''.join([staticpath, docid, ".swf"])
                                    if os.path.exists("/opt/libreoffice3.5/program/python"):
                                        os.system("/opt/libreoffice3.5/program/python /work/Dormforge/util/DocumentConverter.py %s %s" % (usrdoc, usrpdf))
                                    else:
                                        os.system("python /work/Dormforge/util/DocumentConverter.py %s %s" % (usrdoc, usrpdf))
                                    os.system("convert -sample 150x150 %s[0] %s" % (usrpdf, usrjpg))
                                    os.system("pdf2swf %s -o %s -f -T 9 -t -s storeallcharacters" % (usrpdf, usrswf))
                                    os.remove(usrpdf)
                                else:
                                    usrjpg = ''.join([staticpath, docid, ".jpg"])
                                    usrswf = ''.join([staticpath, docid, ".swf"])
                                    os.system("convert -sample 150x150 %s[0] %s" % (usrdoc, usrjpg))
                                    os.system("pdf2swf %s -o %s -f -T 9 -t -s storeallcharacters" % (usrdoc, usrswf))

            if doc_error != 0:
                template_values['doc_error'] = doc_error
                template_values['doc_error_message'] = doc_error_messages[doc_error]
            else:
                if endocid:
                    doc_sql = ["update fd_Doc set "]
                else:
                    if os.path.exists(usrjpg) and os.path.exists(usrswf):
                        doc_sql = ["insert into fd_Doc set doc_id = '%s',name = '%s',content_type = '%s',md5 = '%s', docsize = %s," % (docid,name.replace("'", "''"),content_type,md5,int(size))]
                doc_sql.append("title = '%s'," % title.replace("'", "''"))
                if summary:
                    doc_sql.append("summary = '%s'," % summary.replace("'", "''"))
                if tag:
                    tag = tag.strip().replace(' ',',')
                    tag = tag.strip().replace('，',',')
                    tags = tag.split(",")
                    taglists = []
                    for t in tags:
                        if t in taglists:
                            continue
                        taglists.append(t)
                    newtag = " ".join(taglists)
                    if not (endocid and newtag == oldtag):
                        doc_sql.append("tags = '%s'," % newtag.replace("'", "''"))
                pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
                redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
                doctype = 0
                if secret and secret == "on":
                    doctype = 1
                if endocid:
                    doc_sql.append("status_ = %s where id = %s" % (doctype, decode(endocid)))
                else:
                    doc_sql.append("user_id = %s,pubdate = '%s',status_ = %s" % (self.current_user.id,pubdate,doctype))
                logging.info("".join(doc_sql))
                doc_id = self.db.execute("".join(doc_sql))
                if tag:
                    if (not endocid) or (endocid and newtag != oldtag):
                        for t in taglists:
                            tag_id = self.db.get("select id from fd_Doctag where tag = %s", t)
                            if tag_id:
                                tag_id = tag_id.id
                            else:
                                tag_id = self.db.execute("insert into fd_Doctag (tag) values (%s)", t)
                            if endocid:
                                with_doc_id = decode(endocid)
                            elif doc_id:
                                with_doc_id = doc_id
                            dtag_id = self.db.execute("insert into fd_Dtag (doc_id,tag_id) values (%s,%s)", with_doc_id, tag_id)
                if endocid:
                    doc_key = "doc:%s:%s" % (self.current_user.id, decode(endocid))
                    actdict = {'status':doctype}
                elif doc_id:
                    actdict = {'time':redpubdate, 'docid':docid, 'status':doctype}#docid not doc_id
                if title:
                    actdict['title'] = title
                if summary:
                    actdict['summary'] = summary
                if endocid:
                    if self.rd.hmset(doc_key, actdict):
                        self.redirect("/doc/" + endocid)
                elif doc_id:
                    addresult = add_activity(self.rd, self.current_user.id, doc_id, 4, actdict)
                    if addresult:
                        self.redirect("/doc/" + encode(str(doc_id)))

        if errors != 0:
            if title:
                template_values['title'] = title
            if summary:
                template_values['summary'] = summary
            if tag:
                template_values['tag'] = tag
            self.render("editdoc.html", template_values=template_values)

class DocHandler(BaseHandler):
    def get(self, doc_id):
        template_values = {}
        if len(doc_id) < 8:
            raise tornado.web.HTTPError(404)
        doc_id = decode(doc_id)
        doc = self.db.get("select p.id ,p.name,p.domain,d.title,d.summary,d.status_,d.doc_id "
                ",d.pubdate from fd_People p, fd_Doc d where d.user_id = p.id and "
                "d.id = %s", doc_id)
        if not doc or doc.status_ == 2 or \
        doc.status_ == 1 and doc.name != self.current_user.name:
            raise tornado.web.HTTPError(404)
        template_values['activity'] = doc
        template_values['path'] = self.static_url("usrdoc/%s/%s.swf" % (doc.id, doc.doc_id))
        template_values['epath'] = self.static_url("usrdoc/expressInstall.swf")
        comments = self.db.query("select p.name,p.domain,p.uuid_,p.id,c.comments, "
                "c.pubdate from fd_People p, fd_Doccomm c where p.id"
                "=c.user_id and doc_id = %s", doc_id)
        template_values['comments_length'] = len(comments)
        template_values['comments'] = comments
        self.render("doc.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self, doc_id):
        if len(doc_id) < 8:
            raise tornado.web.HTTPError(404)
        doc_id = decode(doc_id)
        comments = self.get_argument("commenttext",None)
        user_id = self.current_user.id
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        comment_id = self.db.execute("insert into fd_Doccomm (user_id, "
                    " doc_id, comments, pubdate) values (%s,%s,%s,%s)", 
                    user_id, doc_id, comments, pubdate)
        if comment_id:
            doc_key = self.rd.keys('doc*%s' % doc_id)[0]
            prev_comments_num = self.rd.hget(doc_key, 'comm')
            if not prev_comments_num:
                comments_num = 1
            else:
                comments_num = int(prev_comments_num) + 1
            self.rd.hset(doc_key, 'comm', comments_num)
            self.write(''.join([self.avatar('m',self.current_user.id,self.current_user.uuid_), ',', self.br(self.at(linkify(comments, extra_params="target='_blank' rel='nofollow'")))]))

class EditstatusHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        template_values = {}
        statusid = self.get_argument("id",None)
        if not statusid:
            raise tornado.web.HTTPError(404)
        else:
            if len(statusid) < 8:
                raise tornado.web.HTTPError(404)
            status_id = decode(statusid)
            status = self.db.get("select status,user_id,status_ "
                    "from fd_Status where id = %s", status_id)
            if not status or status.user_id != self.current_user.id:
                raise tornado.web.HTTPError(404)
            template_values['status'] = status.status
            template_values['id'] = statusid
        self.render("editstatus.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self):
        statusid = self.get_argument("statusid",None)
        statuscontent = self.get_argument("status",None)
        user_id = self.current_user.id
        if statusid and statuscontent and statuscontent != "":
            statusid = decode(statusid)
            status_user = self.db.get("select user_id from fd_Status where id = %s", statusid)
            if not status_user or status_user.user_id != user_id:
                raise tornado.web.HTTPError(404)
            self.db.execute("update fd_Status set status = %s "
                    "where id = %s", statuscontent, statusid)
            status_key = "status:%s:%s" % (user_id, statusid)
            actdict = {'status':statuscontent}
            if self.rd.hmset(status_key, actdict):
                self.redirect("/status/%s" % encode(statusid))

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
