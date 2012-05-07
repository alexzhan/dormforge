# -*- coding:utf-8 -*-
import tornado.web
import time
import re
import binascii
import uuid
import tempfile
import shutil
import os.path
from util.getby import get_id_by_name
from base import BaseHandler
from util.common import people_number
from util.encrypt import encrypt_password,validate_password
from PIL import Image

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

class FollowBaseHandler(BaseHandler):
    def get(self, domain, follow_type):
        template_values = {}
        people = self.db.get("SELECT id,name,domain,uuid_ FROM fd_People WHERE domain = %s", domain) 
        if not people: raise tornado.web.HTTPError(404)
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
        template_values['is_follow'] = self.ufg.is_follow(self.current_user.id, people.id) if self.current_user else False
        if follow_type == 'following':
            follows = self.ufg.get_follows(template_values['id'])
        elif follow_type == 'follower':
            follows = self.ufg.get_followers(template_values['id'])
        if len(follows) == 0:
            follow_people = []
        else:
            for i in range(people_number):
                if i >= len(follows):
                    break
                follows[i] = int(follows[i])
            if len(follows) == 1:
                follow_people = self.db.query("SELECT id,name,domain,uuid_ from fd_People where id = %s", follows[0]) 
            else:
                orderstr = str(follows[0:people_number])[1:-1].replace(" ","")
                follow_people = self.db.query("SELECT id,name,domain,uuid_ from fd_People where id in %s order by find_in_set(id, %s)", tuple(follows[0:people_number]), orderstr) 
            for i in range(len(follow_people)):
                follow_people[i].is_follow = self.ufg.is_follow(self.current_user.id, follow_people[i].id) if self.current_user else False
                follow_people[i].image = self.avatar("m", follow_people[i].id, follow_people[i].uuid_)
                if not self.current_user or self.current_user and self.current_user.id != follow_people[i].id:
                    follow_people[i].is_self = False 
                else:
                    follow_people[i].is_self = True
        template_values['people'] = follow_people 
        template_values['type'] = follow_type 
        template_values['people_count'] = len(follows)
        template_values['lastindex'] = people_number
        template_values['hasnext'] = 1
        if template_values['lastindex'] >= len(follows):
            template_values['hasnext'] = 0
        self.render("follow.html", template_values=template_values)

class SettingModule(tornado.web.UIModule):
    def render(self, template_values):
        return self.render_string("modules/%s.html" % template_values['setting'], template_values=template_values)

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
            template_values['selfdesc'] = selfdesc.selfdesc
        isself = template_values['id'] == self.current_user.id if self.current_user else False
        template_values['activities'] = self.uag.get_top_activities(template_values['id'], self.db, isself, 0, 5) 
        template_values['activity_count'] = self.uag.count_activity(template_values['id']) 
        template_values['statuses'] = self.uag.get_top_sub_activities(template_values['id'], 1, isself, 0, 3) 
        template_values['status_count'] = self.uag.count_sub_activity(template_values['id'], 1) 
        template_values['notes'] = self.uag.get_top_sub_activities(template_values['id'], 2, isself, 0, 3) 
        template_values['note_count'] = self.uag.count_sub_activity(template_values['id'], 2) 
        template_values['links'] = self.uag.get_top_sub_activities(template_values['id'], 3, isself, 0, 3) 
        template_values['link_count'] = self.uag.count_sub_activity(template_values['id'], 3) 
        template_values['docs'] = self.uag.get_top_sub_activities(template_values['id'], 4, isself, 0, 3) 
        template_values['doc_count'] = self.uag.count_sub_activity(template_values['id'], 4) 
        self.render("people.html", template_values=template_values)

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
            people = self.db.query("SELECT SQL_CALC_FOUND_ROWS id,name,domain,uuid_ FROM fd_People WHERE (city_id=%s and college_type=1) or (ss_city_id=%s and college_type=2) or (bs_city_id=%s and college_type=3) limit 0,%s", region_id, region_id, region_id, people_number) 
        elif region == "college":
            image_path = region_get.image_path
            people = self.db.query("SELECT SQL_CALC_FOUND_ROWS id,name,domain,uuid_ FROM fd_People WHERE (college_id=%s and college_type=1) or (ss_college_id=%s and college_type=2) or (bs_college_id=%s and college_type=3) limit 0,%s", region_id, region_id, region_id, people_number)
        elif region == "major":
            people = self.db.query("SELECT SQL_CALC_FOUND_ROWS id,name,domain,uuid_ FROM fd_People WHERE (major_id=%s and college_type=1) or (ss_major_id=%s and college_type=2) or (bs_major_id=%s and college_type=3) limit 0,%s", region_id, region_id, region_id, people_number) 
        people_count = self.db.get("select found_rows() as length").length
        template_values = {}
        template_values['region_id'] = region_id
        template_values['region'] = name
        template_values['type'] = region
        template_values['people_count'] = people_count
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
        template_values['lastindex'] = people_number
        template_values['hasnext'] = 1
        if template_values['lastindex'] >= people_count:
            template_values['hasnext'] = 0
        self.render("region.html", template_values=template_values)
