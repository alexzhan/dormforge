from base import BaseHandler
import tornado.web
import time
from util.encode import encode,decode
from util.redis_activity import add_activity
from tornado.escape import linkify

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
