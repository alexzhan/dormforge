# -*- coding:utf-8 -*-
from base import BaseHandler
import tornado.web
from util.encode import decode
import time
from util.redis_activity import add_activity
from tornado.escape import linkify

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
            link_sql = ["update fd_Link set url = '{0}',".format(url.replace('%','%%'))]
        else:
            link_sql = ["insert into fd_Link set url = '{0}',".format(url.replace('%','%%'))]
        if title:
            link_sql.append("title = '{0}',".format(title.replace("'", "''").replace('%','%%')))
        if summary:
            link_sql.append("summary = '{0}',".format(summary.replace("'", "''").replace('%','%%')))
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
                link_sql.append("tags = '{0}',".format(newtag.replace("'", "''").replace('%','%%')))
        pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
        redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
        if pubtype == 2:
            link_sql.append("status_ = {0} where id = {1}".format(linktype,linkid))
        else:
            link_sql.append("user_id = {0},pubdate = '{1}',status_ = {2}".format(self.current_user.id,pubdate,linktype))
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


