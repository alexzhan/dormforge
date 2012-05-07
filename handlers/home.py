import tornado.web
import time
from base import BaseHandler
from util.common import feed_number

class HomeHandler(BaseHandler):
    def get(self):
        if self.current_user:
            template_values = {}
            template_values['all_activities'] = self.uag.get_all_activities(self.db, 0, False)
            template_values['lastindex'] = feed_number
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= self.uag.count_all_activity():
                template_values['hasnext'] = 0
            template_values['lastitem'] = self.uag.count_all_activity()
            self.render("home.html", template_values=template_values)
        else:
            self.render("index.html")

class MyhomeHandler(BaseHandler):
    def get(self):
        if self.current_user:
            template_values = {}
            template_values['all_activities'] = self.uag.get_my_activities(self.db, self.current_user.id, 0)
            template_values['lastindex'] = feed_number
            template_values['hasnext'] = 1
            if template_values['lastindex'] >= self.uag.count_my_activity(self.current_user.id):
                template_values['hasnext'] = 0
            self.render("myhome.html", template_values=template_values)
        else:
            self.render("index.html")

class HomepollHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        self.get_data(callback=self.to_finish)
    def get_data(self, callback):
        if self.request.connection.stream.closed():
            return
        template_values = {}
        lastitem = self.get_argument("lastitem",None)
        lastitem = int(lastitem)
        newcount = self.uag.count_all_activity()
        if lastitem < newcount: #something added,add the feed and refresh the lastitem number
            new_activities = self.uag.get_all_activities(self.db, lastitem, newcount-lastitem)
            new_activities = filter(lambda activity:activity[-2] != 'status' and activity[-6] != self.current_user.id, new_activities) #if user add a status,it's been shown just after it's been published,so it cannot be shown again by longpolling even the user opens another browser window.
            template_values['all_activities'] = new_activities
            template_values['ifnext'] = 0
            template_values['lastitem'] = newcount
        elif lastitem > newcount: #something deleted,refresh the lastitem number
            template_values['all_activities'] = {}
            template_values['ifnext'] = 0
            template_values['lastitem'] = newcount
        callback(template_values)
    def to_finish(self, data):
        if 'lastitem' in data:
            self.render("modules/home_activities.html", template_values=data)
        else:
            tornado.ioloop.IOLoop.instance().add_timeout(
                    time.time()+5, #recheck after 5 seconds
                    lambda: self.get_data(callback=self.to_finish),
                    )
