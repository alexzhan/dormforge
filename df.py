#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os.path
import re
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

from tornado.options import define, options
from util.encrypt import encrypt_password,validate_password
from db.redis.user_follow_graph import UserFollowGraph
from db.redis.user_activity_graph import UserActivityGraph

define("port", default=80, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="df", help="blog database name")
define("mysql_user", default="df", help="blog database user")
define("mysql_password", default="df", help="blog database password")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/", HomeHandler),
                (r"/signup", SignupHandler),
                (r"/login", LoginHandler),
                (r"/logout", LogoutHandler),
                (r"/contact", ContactHandler),
                (r"/about", AboutHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)", PeopleHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)/following", FollowingHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)/follower", FollowerHandler),
                (r"/city/(.*)", CityHandler),
                (r"/college/(.*)", CollegeHandler),
                (r"/major/(.*)", MajorHandler),
                (r"/isidexist", UsernameExistHandler),
                (r"/isemailexist", EmailExistHandler),
                (r"/isdomainexist", DomainExistHandler),
                (r"/iscollegeexist", CollegeExistHandler),
                (r"/follow", FollowHandler),
                (r"/unfollow", UnfollowHandler),
                (r"/selfdesc", SelfdescHandler),
                (r"/3e224bd553a3bfca3c7cb92c9806cd04\.html", CdnzzVerifyHandler),
                ]
        settings = dict(
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
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

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: return None
        return self.db.get("SELECT * FROM fd_People WHERE id = %s", int(user_id))

    def set_default_headers(self): 
        self.set_header('Server', '18zhouServer/1.1')

class UserBaseHandler(BaseHandler):
    def people(self, domain):
        people = self.db.get("SELECT * FROM fd_People WHERE domain = %s", domain) 
        if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        if not self.get_secure_cookie("user") or self.get_secure_cookie("user") and int(self.get_secure_cookie("user")) != int(people.id):
            template_values['is_self'] = False
        else:
            template_values['is_self'] = True
        template_values['id'] = people.id
        template_values['username'] = people.name
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

        ufg = UserFollowGraph(self.rd)
        template_values['follow_count'] = ufg.follow_count(people.id)
        template_values['follower_count'] = ufg.follower_count(people.id)
        template_values['is_follow'] = ufg.is_follow(self.get_secure_cookie("user"), people.id)
        return template_values

class FollowBaseHandler(BaseHandler):
    def follow(self, domain, follow_type):
        people = self.db.get("SELECT id,name FROM fd_People WHERE domain = %s", domain) 
        if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        if not self.get_secure_cookie("user") or self.get_secure_cookie("user") and int(self.get_secure_cookie("user")) != int(people.id):
            template_values['is_self'] = False
        else:
            template_values['is_self'] = True
        template_values['id'] = people.id
        template_values['username'] = people.name
        template_values['image'] = self.static_url("img/no_avatar.jpg")
        ufg = UserFollowGraph(self.rd)
        template_values['follow_count'] = ufg.follow_count(people.id)
        template_values['follower_count'] = ufg.follower_count(people.id)
        template_values['is_follow'] = ufg.is_follow(self.get_secure_cookie("user"), people.id)
        if follow_type == 'following':
            follows = ufg.get_follows(template_values['id'])
        elif follow_type == 'follower':
            follows = ufg.get_followers(template_values['id'])
        if len(follows) == 0:
            follow_people = []
        else:
            idstr = "".join(["(", "%s,"*(len(follows)-1), "%s", ")"])
            #logging.info("SELECT name from fd_People where id in " + idstr % tuple(follows))
            follow_people = self.db.query("SELECT id,name from fd_People where id in " + idstr % tuple(follows)) 
            for i in range(len(follow_people)):
                follow_people[i].is_follow = ufg.is_follow(self.get_secure_cookie("user"), follow_people[i].id)
                follow_people[i].image = self.static_url("img/no_avatar.jpg")
                if not self.get_secure_cookie("user") or self.get_secure_cookie("user") and int(self.get_secure_cookie("user")) != int(follow_people[i].id):
                    follow_people[i].is_self = False 
                else:
                    follow_people[i].is_self = True
        template_values['follow'] = follow_people 
        template_values['type'] = follow_type 
        return template_values

class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")

class SignupHandler(BaseHandler):
    def get(self):
        if self.current_user:
            return self.redirect("people/" + self.current_user.domain)
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
                if (p.search(email)):
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
                    domain_id = self.db.get("select id from fd_People where domain = %s", domain)
                    if(domain_id):
                        errors = errors + 1
                        domain_error = 4 
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
        signup_date = time.strftime('%Y-%m-%d %X', time.localtime())
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
            return self.redirect("people/" + self.current_user.domain)
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
            login_date = time.strftime('%Y-%m-%d %X', time.localtime())
            self.db.execute(
                    "UPDATE fd_People SET login_ip = %s, login_date = %s WHERE id = %s", login_ip, login_date, people['id'])
            self.set_secure_cookie("user", str(people['id']))
            next_url = self.get_argument("next", "people/" + str(people['domain']))
            if next_url == '/':
                self.redirect("people/" + str(people['domain']))
            else:
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
        nowtime = time.strftime('%Y-%m-%d %X', time.localtime())
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
                template_values = {}
                template_values['message'] = '您的反馈我们已收到，谢谢！'
                self.render("success.html", template_values=template_values)

class AboutHandler(BaseHandler):
    def get(self):
        self.render("about.html")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("_xsrf")
        self.redirect(self.get_argument("next", "/"))

class PeopleHandler(UserBaseHandler):
    def get(self, domain):
        template_values = self.people(domain)    
        template_values['image'] = self.static_url("img/no_avatar.jpg")
        template_values['selfdesc'] = ""
        if template_values['has_selfdesc']:
            selfdesc = self.db.get("select selfdesc from fd_Selfdesc where user_id = %s", 
                    template_values['id'])
            if not selfdesc: raise tornado.web.HTTPError(405)
            template_values['selfdesc'] = selfdesc.selfdesc
        uag = UserActivityGraph(self.rd)
        template_values['activities'] = uag.get_top_activities(template_values['id']) 
        template_values['activity_count'] = uag.count_activity(template_values['id']) 
        self.render("people.html", template_values=template_values)

class FollowingHandler(FollowBaseHandler):
    def get(self, domain):
        template_values = self.follow(domain, 'following')
        self.render("follow.html", template_values=template_values)

class FollowerHandler(FollowBaseHandler):
    def get(self, domain):
        template_values = self.follow(domain, 'follower')
        self.render("follow.html", template_values=template_values)

class CityHandler(BaseHandler):
    def get(self, city):
        city_id = self.db.get("SELECT id FROM fd_City where name = %s", city)
        if not city_id: raise tornado.web.HTTPError(404)
        city_id = city_id.id
        people = self.db.query("SELECT id,name FROM fd_People WHERE (city_id=%s and college_type=1) or (ss_city_id=%s and college_type=2) or (bs_city_id=%s and college_type=3)", city_id, city_id, city_id) 
        #if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        template_values['region_id'] = city_id
        template_values['region'] = city
        template_values['type'] = 'city'
        template_values['image'] = self.static_url("img/no_photo.gif")
        ufg = UserFollowGraph(self.rd)
        for i in range(len(people)):
            people[i].is_follow = ufg.is_follow(self.get_secure_cookie("user"), people[i].id)
            people[i].image = self.static_url("img/no_avatar.jpg")
            if not self.get_secure_cookie("user") or self.get_secure_cookie("user") and int(self.get_secure_cookie("user")) != int(people[i].id):
                people[i].is_self = False 
            else:
                people[i].is_self = True
        template_values['people'] = people 
        self.render("region.html", template_values=template_values)

class CollegeHandler(BaseHandler):
    def get(self, college):
        college_id = self.db.get("SELECT id,image_path FROM fd_College where name = %s", college)
        if not college_id: raise tornado.web.HTTPError(404)
        image_path = college_id.image_path
        college_id = college_id.id
        people = self.db.query("SELECT id,name FROM fd_People WHERE (college_id=%s and college_type=1) or (ss_college_id=%s and college_type=2) or (bs_college_id=%s and college_type=3)", college_id, college_id, college_id) 
        #if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        template_values['region_id'] = college_id
        template_values['region'] = college
        template_values['type'] = 'college'
        if image_path:
            template_values['image'] = self.static_url("schoolimage/" + image_path)
        else:
            template_values['image'] = self.static_url("img/no_photo.gif")
        ufg = UserFollowGraph(self.rd)
        for i in range(len(people)):
            people[i].is_follow = ufg.is_follow(self.get_secure_cookie("user"), people[i].id)
            people[i].image = self.static_url("img/no_avatar.jpg")
            if not self.get_secure_cookie("user") or self.get_secure_cookie("user") and int(self.get_secure_cookie("user")) != int(people[i].id):
                people[i].is_self = False 
            else:
                people[i].is_self = True
        template_values['people'] = people 
        self.render("region.html", template_values=template_values)

class MajorHandler(BaseHandler):
    def get(self, major):
        major_id = self.db.get("SELECT id FROM fd_Major where name = %s", major)
        if not major_id: raise tornado.web.HTTPError(404)
        major_id = major_id.id
        people = self.db.query("SELECT id,name FROM fd_People WHERE (major_id=%s and college_type=1) or (ss_major_id=%s and college_type=2) or (bs_major_id=%s and college_type=3)", major_id, major_id, major_id) 
        #if not people: raise tornado.web.HTTPError(404)
        template_values = {}
        template_values['region_id'] = major_id
        template_values['region'] = major
        template_values['type'] = 'major'
        template_values['image'] = self.static_url("img/no_photo.gif")
        ufg = UserFollowGraph(self.rd)
        for i in range(len(people)):
            people[i].is_follow = ufg.is_follow(self.get_secure_cookie("user"), people[i].id)
            people[i].image = self.static_url("img/no_avatar.jpg")
            if not self.get_secure_cookie("user") or self.get_secure_cookie("user") and int(self.get_secure_cookie("user")) != int(people[i].id):
                people[i].is_self = False 
            else:
                people[i].is_self = True
        template_values['people'] = people 
        self.render("region.html", template_values=template_values)

class UsernameExistHandler(BaseHandler):
    def post(self):
        username = self.get_argument("username",None)
        user_id = self.db.get("select id from fd_People where name = %s", username)
        if user_id:
            self.write("已被占用")
        else: 
            self.write("可以使用")

class EmailExistHandler(BaseHandler):
    def post(self):
        email = self.get_argument("email",None)
        user_id = self.db.get("select id from fd_People where email = %s", email)
        if user_id:
            self.write("该邮箱已被人注册")
        else: 
            self.write("可以使用")

class DomainExistHandler(BaseHandler):
    def post(self):
        domain = self.get_argument("domain",None)
        user_id = self.db.get("select id from fd_People where domain = %s", domain)
        if user_id:
            self.write("已被占用")
        else: 
            self.write("可以使用")

class CollegeExistHandler(BaseHandler):
    def post(self):
        college = self.get_argument("college",None)
        college_id = self.db.get("select id from fd_College where name = %s", college)
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
        ufg = UserFollowGraph(self.rd)
        if ufg.follow(from_user, to_user):
            acttime = time.strftime('%Y-%m-%d %X', time.localtime()) 
            actto = self.db.get("select name from fd_People where id = %s", to_user).name
            actdict = { 'type':1, 'time':acttime, 'to':actto }
            add_activity(self.rd, from_user, actdict)
        else:
            self.write('already')

class UnfollowHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        from_user = self.get_argument("from_user",None)
        to_user = self.get_argument("to_user",None)
        if from_user == to_user or from_user == 0 or to_user == 0: raise tornado.web.HTTPError(405)
        ufg = UserFollowGraph(self.rd)
        if ufg.unfollow(from_user, to_user):
            actto = self.db.get("select name from fd_People where id = %s", to_user).name
            del_activity(self.rd, from_user, "1", actto)
        else:
            self.write('already')

class SelfdescHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        selfdesc = self.get_argument("selfdesc",None)
        if not selfdesc: raise tornado.web.HTTPError(405)
        #logging.info("%s", self.current_user.has_selfdesc)
        if self.current_user.has_selfdesc:
            self.db.execute("update fd_Selfdesc set selfdesc = %s"
                    "where user_id = %s", selfdesc, self.current_user.id)
        else:
            selfdesc_id = self.db.execute("insert into fd_Selfdesc (user_id, selfdesc)"
                    " values (%s,%s)", self.current_user.id, selfdesc)
            if selfdesc_id:
                self.db.execute("update fd_People set has_selfdesc"
                        " = 1 where id = %s", self.current_user.id)

class CdnzzVerifyHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('e1faafa0c2f808702da5c1b7fda8e919')

def add_activity(client, actuser, actdict):
    uag = UserActivityGraph(client)
    return uag.add_activity(actuser, actdict)

def del_activity(client, actuser ,acttype, actto):
    uag = UserActivityGraph(client)
    return uag.del_activity(actuser, acttype, actto)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
