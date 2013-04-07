#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os.path
import sys
import string
import torndb
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata

from tornado.options import define, options

from handlers.base import BaseHandler
from handlers.home import HomeHandler,MyhomeHandler,HomepollHandler
from handlers.account import FollowBaseHandler,SignupHandler,LoginHandler,SettingsHandler,LogoutHandler,PeopleHandler,RegionHandler,SettingModule
from handlers.front import ContactHandler,AboutHandler,PNFHandler,HeroHandler
from handlers.action import MoreHandler,ExistHandler,FollowHandler,UnfollowHandler,SelfdescHandler,DeleteActivityHandler,ViewnoteHandler,CansugHandler
from handlers.status import PubstatusHandler,StatusHandler,EditstatusHandler
from handlers.link import EditlinkHandler,LinkHandler
from handlers.note import PubnoteHandler,NoteHandler,NotehistoryHandler
from handlers.doc import EditdocHandler,DocHandler
from handlers.activity import ActivityHandler

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
                (r"/hero(/[0-9]+)?", HeroHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)", PeopleHandler),
                (r"/people/([a-z0-9A-Z\_\-]+)/(following|follower)", FollowBaseHandler),
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
                (r"/people/([a-z0-9A-Z\_\-]+)/(activity|status|note|link|doc)", ActivityHandler),
                (r"/homepoll", HomepollHandler),
                (r"/note/([0-9a-z]+)/log", NotehistoryHandler),
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
        self.db = torndb.Connection(
                host=options.mysql_host, database=options.mysql_database,
                user=options.mysql_user, password=options.mysql_password)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
