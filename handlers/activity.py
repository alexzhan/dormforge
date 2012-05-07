# -*- coding:utf-8 -*-
from base import BaseHandler
import tornado.web
from util.common import activity_number

class ActivityHandler(BaseHandler):
    def get(self, domain, activity_type):
        Activities = ["活动","状态","日志","链接","文档"]
        activities = ["activity","status","note","link","doc"]
        template_values = {}
        people = self.db.get("SELECT id,name,domain,uuid_ FROM fd_People WHERE domain = %s", domain) 
        if not people: raise tornado.web.HTTPError(404)
        if not self.current_user or self.current_user and self.current_user.id != people.id:
            template_values['is_self'] = False
        else:
            template_values['is_self'] = True
        page_title = "%s - %s" % (people.name, Activities[activities.index(activity_type)])
        template_values['page_title'] = page_title
        template_values['id'] = people.id
        template_values['uuid'] = people.uuid_
        template_values['username'] = people.name
        template_values['domain'] = people.domain
        template_values['image'] = self.avatar("xl", people.id, people.uuid_)
        template_values['is_follow'] = self.ufg.is_follow(self.current_user.id, people.id) if self.current_user else False
        if activity_type == "activity":
            activity_count = self.uag.count_activity(template_values['id'])
            template_values['activities'] = self.uag.get_top_activities(template_values['id'], self.db, template_values['is_self'], 0, activity_number) 
        else:
            activity_count = self.uag.count_sub_activity(template_values['id'], activities.index(activity_type)) 
            template_values['activities'] = self.uag.get_top_sub_activities(template_values['id'], activities.index(activity_type), template_values['is_self'], 0, activity_number) 
        template_values['profile_text'] = "%s %s" % (Activities[activities.index(activity_type)], activity_count)
        template_values['activity_type'] = activity_type
        template_values['lastindex'] = activity_number
        template_values['hasnext'] = 1
        if template_values['lastindex'] >= activity_count:
            template_values['hasnext'] = 0
        self.render("activity.html", template_values=template_values)
