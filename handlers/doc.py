# -*- coding:utf-8 -*-
from base import BaseHandler
import tornado.web
import time
import os.path
import shutil
from util.encode import decode,encode
from util.redis_activity import add_activity
from tornado.escape import linkify

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
                        doc_sql = ["insert into fd_Doc set doc_id = '%s',name = '%s',content_type = '%s',md5 = '%s', docsize = %s," % (docid,name.replace("'", "''").replace("%", "%%"),content_type,md5,int(size))]
                doc_sql.append("title = '%s'," % title.replace("'", "''").replace("%", "%%"))
                if summary:
                    doc_sql.append("summary = '%s'," % summary.replace("'", "''").replace("%", "%%"))
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
                        doc_sql.append("tags = '%s'," % newtag.replace("'", "''").replace("%", "%%"))
                pubdate = time.strftime('%y-%m-%d %H:%M', time.localtime())
                redpubdate = pubdate[4:] if pubdate[3] == '0' else pubdate[3:]
                doctype = 0
                if secret and secret == "on":
                    doctype = 1
                if endocid:
                    doc_sql.append("status_ = %s where id = %s" % (doctype, decode(endocid)))
                else:
                    doc_sql.append("user_id = %s,pubdate = '%s',status_ = %s" % (self.current_user.id,pubdate,doctype))
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

