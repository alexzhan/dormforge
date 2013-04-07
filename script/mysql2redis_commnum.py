import torndb
import redis

from tornado.options import define, options

define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="df", help="blog database name")
define("mysql_user", default="df", help="blog database user")
define("mysql_password", default="df", help="blog database password")

db = torndb.Connection(
        host=options.mysql_host, database=options.mysql_database,
        user=options.mysql_user, password=options.mysql_password)

rd = redis.StrictRedis(host='localhost', port=6379, db=0)

for status_key in rd.keys("status*"):
    status_id = status_key.split(":")[-1]
    comments = db.query("select id from fd_Stacomm where status_id = %s", status_id)
    rd.hset(status_key, 'comm', len(comments))
