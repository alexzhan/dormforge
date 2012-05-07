# -*- coding:utf-8 -*-
import tornado.web
import time
import os.path
from base import BaseHandler
from tornado.escape import xhtml_escape,linkify
from util.getby import get_id_by_name,get_domain_by_name,get_namedomainuuid_by_id
from util.redis_activity import add_activity,del_activity
from util.common import feed_number,people_number,activity_number
from util.encode import decode

class MoreHandler(BaseHandler):
    def get(self, prop):
        template_values = {}
        startindex = self.get_argument("lastindex", None)
        startindex = int(startindex)
        if prop in ["home", "myhome"]:
            if prop == "home":
                template_values['all_activities'] = self.uag.get_all_activities(self.db, startindex, False)
            elif prop == "myhome":
                template_values['all_activities'] = self.uag.get_my_activities(self.db, self.current_user.id, startindex)
            template_values['lastindex'] = startindex + feed_number
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= self.uag.count_all_activity():
                template_values['hasnext'] = 0
            self.render("modules/home_activities.html", template_values=template_values)
        elif prop in ["city", "college", "major"]:
            name = self.get_argument("name", None)
            region = prop
            if region == "college":
                region_get = self.db.get("SELECT id,image_path FROM fd_College where name = %s", name)
            elif region == "city":
                region_get = self.db.get("SELECT id FROM fd_City where name = %s", name)
            elif region == "major":
                region_get = self.db.get("SELECT id FROM fd_Major where name = %s", name)
            if not region_get: raise tornado.web.HTTPError(404)
            region_id = region_get.id
            if region == "city": 
                people = self.db.query("SELECT SQL_CALC_FOUND_ROWS id,name,domain,uuid_ FROM fd_People WHERE (city_id=%s and college_type=1) or (ss_city_id=%s and college_type=2) or (bs_city_id=%s and college_type=3) limit %s,%s", region_id, region_id, region_id, startindex, people_number) 
            elif region == "college":
                people = self.db.query("SELECT SQL_CALC_FOUND_ROWS id,name,domain,uuid_ FROM fd_People WHERE (college_id=%s and college_type=1) or (ss_college_id=%s and college_type=2) or (bs_college_id=%s and college_type=3) limit %s,%s", region_id, region_id, region_id, startindex, people_number)
            elif region == "major":
                people = self.db.query("SELECT SQL_CALC_FOUND_ROWS id,name,domain,uuid_ FROM fd_People WHERE (major_id=%s and college_type=1) or (ss_major_id=%s and college_type=2) or (bs_major_id=%s and college_type=3) limit %s,%s", region_id, region_id, region_id, startindex, people_number) 
            people_count = self.db.get("select found_rows() as length").length
            for i in range(len(people)):
                people[i].is_follow = self.ufg.is_follow(self.current_user.id, people[i].id) if self.current_user else False
                people[i].image = self.avatar("m", people[i].id, people[i].uuid_)
                if not self.current_user or self.current_user and self.current_user.id != people[i].id:
                    people[i].is_self = False
                else:
                    people[i].is_self = True
            template_values['people'] = people
            template_values['lastindex'] = startindex + people_number
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= people_count:
                template_values['hasnext'] = 0
            self.render("modules/follow_people.html", template_values=template_values)
        elif prop in ["following", "follower"]:
            follow_type = prop
            people_id = self.get_argument("name", None)
            if follow_type == 'following':
                follows = self.ufg.get_follows(people_id)
            elif follow_type == 'follower':
                follows = self.ufg.get_followers(people_id)
            follow_people = []
            for i in range(startindex, startindex+people_number):
                if i >= len(follows):
                    break
                follows[i] = int(follows[i])
            if len(follows) - startindex == 1:
                follow_people = self.db.query("SELECT id,name,domain,uuid_ from fd_People where id = %s", follows[startindex]) 
            else:
                orderstr = str(follows[startindex:startindex+people_number])[1:-1].replace(" ","")
                follow_people = self.db.query("SELECT id,name,domain,uuid_ from fd_People where id in %s order by find_in_set(id, %s)", tuple(follows[startindex:startindex+people_number]), orderstr) 
            for i in range(len(follow_people)):
                follow_people[i].is_follow = self.ufg.is_follow(self.current_user.id, follow_people[i].id) if self.current_user else False
                follow_people[i].image = self.avatar("m", follow_people[i].id, follow_people[i].uuid_)
                if not self.current_user or self.current_user and self.current_user.id != follow_people[i].id:
                    follow_people[i].is_self = False 
                else:
                    follow_people[i].is_self = True
            template_values['people'] = follow_people 
            template_values['lastindex'] = startindex + people_number
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= len(follows):
                template_values['hasnext'] = 0
            self.render("modules/follow_people.html", template_values=template_values)
        elif prop in ["activity", "status", "note", "link", "doc"]:
            activities = ["activity","status","note","link","doc"]
            people_id = self.get_argument("name", None)
            isself = self.get_argument("isself", None)
            if isself == "True": isself = True
            elif isself == "False": isself = False
            else: raise tornado.web.HTTPError(404)
            username,domain,uuid = get_namedomainuuid_by_id(self.db, self.rd, people_id)
            template_values['domain'] = domain
            template_values['username'] = username
            if prop == "activity":
                activity_count = self.uag.count_activity(people_id)
                template_values['activities'] = self.uag.get_top_activities(people_id, self.db, isself, startindex, activity_number) 
            else:
                activity_count = self.uag.count_sub_activity(people_id, activities.index(prop)) 
                template_values['activities'] = self.uag.get_top_sub_activities(people_id, activities.index(prop), isself, startindex, activity_number) 
            template_values['activity_type'] = prop
            template_values['lastindex'] = startindex + activity_number
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= activity_count:
                template_values['hasnext'] = 0
            self.render("modules/people_activities.html", template_values=template_values)

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
        self.write(self.br(xhtml_escape(selfdesc)).strip())

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

class ViewnoteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
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

class CansugHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        self.current_user.sugg_link = 1
        self.db.execute("update fd_People set sugg_link = 1 where id = %s", self.current_user.id)
