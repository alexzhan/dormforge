from base import BaseHandler
import tornado.web
from util.common import hero_number

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
        nowtime = time.strftime('%y-%m-%d %H:%M', time.localtime())
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
                self.write("right")

class AboutHandler(BaseHandler):
    def get(self):
        self.render("about.html")

class PNFHandler(BaseHandler):
    def get(self):
        self.set_status(404)
        self.render("404.html")

class HeroHandler(BaseHandler):
    def get(self, page):
        template_values = {}
        if not page:
            page = 1
        else:
            page = int(page[1:])
        people = self.db.query("select SQL_CALC_FOUND_ROWS * from fd_People order by id limit %s,%s", (int(page)-1)*hero_number, hero_number)
        people_count = self.db.get("select found_rows() as length").length
        page_count = (people_count + hero_number - 1)/hero_number
        for i in range(len(people)):
            coltype = people[i].college_type
            if coltype == 1:
                c1 = self.db.get("select name from fd_City where id = %s", people[i].city_id)
                c2 = self.db.get("select name from fd_College where id = %s", people[i].college_id)
                c3 = self.db.get("select name from fd_Major where id = %s", people[i].major_id)
            elif coltype == 2:
                c1 = self.db.get("select name from fd_City where id = %s", people[i].ss_city_id)
                c2 = self.db.get("select name from fd_College where id = %s", people[i].ss_college_id)
                c3 = self.db.get("select name from fd_Major where id = %s", people[i].ss_major_id)
            elif coltype == 3:
                c1 = self.db.get("select name from fd_City where id = %s", people[i].bs_city_id)
                c2 = self.db.get("select name from fd_College where id = %s", people[i].bs_college_id)
                c3 = self.db.get("select name from fd_Major where id = %s", people[i].bs_major_id)
            elif coltype == 4:
                c1 = people[i].zx_city
                c2 = people[i].zx_school
                c3 = self.db.get("select name from fd_Province where id = %s", people[i].zx_province_id)
            people[i].c3 = c3.name
            if coltype == 4:
                people[i].c1 = c1
                people[i].c2 = c2
            else:
                people[i].c1 = c1.name
                people[i].c2 = c2.name
        template_values['people'] = people
        template_values['page'] = page
        template_values['page_count'] = page_count
        self.render("hero.html", template_values=template_values)
