from base import BaseHandler
import tornado.web
import time
from util.encode import decode,encode
from util.redis_activity import add_activity
from util.getby import get_namedomainuuid_by_id
from tornado.escape import linkify,xhtml_escape
from util.textdiff import textdiff

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
        rev_user = get_namedomainuuid_by_id(self.db,self.rd,str(user_id))
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        if noteid:
            noteid = decode(noteid)
            note_user = self.db.get("select user_id from fd_Note where id = %s", noteid)
            if not note_user or note_user.user_id != user_id:
                raise tornado.web.HTTPError(404)
            self.db.execute("update fd_Note set title = %s, note = %s,"
                    "status_ = %s where id = %s", notetitle, notecontent, status_, noteid)
            rev_num = int(self.db.get("select max(rev_num) as rev_num from fd_NoteHistory where note_id = %s", noteid).rev_num)
            self.db.execute("insert into fd_NoteHistory(note_id,title,note,rev_num,rev_user_id,"
                    "rev_user_name,rev_user_domain,revdate) values (%s,%s,%s,%s,%s,%s,%s,%s)", noteid, notetitle,
                    notecontent, rev_num+1, user_id, rev_user[0], rev_user[1], pubdate)
            note_key = "note:%s:%s" % (user_id, noteid)
            actdict = {'title':notetitle, 'content':rednotecontent, 'status':status_}
            if self.rd.hmset(note_key, actdict):
                self.write("right")
            else:
                self.write("wrong")
        else:
            redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
            note_id = self.db.execute("insert into fd_Note (user_id, title, "
                    "note, pubdate, status_) values (%s,%s,%s,%s,%s)", user_id,
                    notetitle, notecontent, pubdate, status_)
            if note_id:
                self.db.execute("insert into fd_NoteHistory(note_id,title,note,rev_num,rev_user_id,"
                        "rev_user_name,rev_user_domain,revdate) values (%s,%s,%s,%s,%s,%s,%s,%s)", note_id, notetitle,
                        notecontent, 1, user_id, rev_user[0], rev_user[1], pubdate)
                actdict = {'time':redpubdate, 'title':notetitle, 
                        'content':rednotecontent, 'status':status_}
                addresult = add_activity(self.rd, user_id, note_id, 2, actdict)
                if addresult:
                    self.write(encode(str(note_id)))
                    #self.write("right")
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

class NotehistoryHandler(BaseHandler):
    def get(self, note_id):
        template_values = {}
        if len(note_id) < 8:
            raise tornado.web.HTTPError(404)
        note_id = decode(note_id)
        notes = self.db.query(
                "select title,note,rev_num,rev_user_name as name,rev_user_domain as domain"
                ", revdate from fd_NoteHistory where note_id = %s and rev_status = 0"
                " order by rev_num desc", note_id)
        if not notes:
            raise tornado.web.HTTPError(404)
        for i in range(len(notes)):
            next_note = {}
            if i == len(notes)-1:
                next_note['title'] = ''
                next_note['note'] = ''
            else:
                next_note['title'] = notes[i+1].title
                next_note['note'] = notes[i+1].note
            notes[i].title = textdiff(xhtml_escape(next_note['title']), xhtml_escape(notes[i].title))
            note1 = self.br(linkify(next_note['note'], extra_params="target='_blank' rel='nofollow'"))
            note2 = self.br(linkify(notes[i].note, extra_params="target='_blank' rel='nofollow'"))
            notes[i].note = self.at(textdiff(note1, note2))
            notes[i]['rev'] = 0
            if i == 0:
                notes[i]['rev'] = 1
        template_values['notes'] = notes
        self.render("notehistory.html", template_values=template_values)
    @tornado.web.authenticated
    def post(self, note_id):
        version = self.get_argument("version",None)
        if len(note_id) < 8 or not version:
            raise tornado.web.HTTPError(404)
        note_id = decode(note_id)
        user = self.db.get("select user_id from fd_Note where id = %s", note_id)
        #only owner and administrator can revert
        if user.user_id != self.current_user.id and self.current_user.actlevel != 0:
            return self.write("nopermit")
        self.db.execute("update fd_NoteHistory set rev_status = 1 where note_id = %s and rev_num > %s"
                , note_id, version)
        note = self.db.get("select title,note from fd_NoteHistory where note_id = %s and rev_num = %s"
                , note_id, version)
        self.db.execute("update fd_Note set title = %s, note = %s where id = %s", note.title, note.note, note_id)
        note_key = "note:%s:%s" % (user.user_id, note_id)
        rednotecontent = note.note
        if len(note.note) > 150:
            rednotecontent = note.note[:140] + " ..."
        actdict = {'title':note.title, 'content':rednotecontent}
        self.rd.hmset(note_key, actdict)
