import tornado.database
import redis

from tornado.options import define, options

define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="df", help="blog database name")
define("mysql_user", default="df", help="blog database user")
define("mysql_password", default="df", help="blog database password")

db = tornado.database.Connection(
        host=options.mysql_host, database=options.mysql_database,
        user=options.mysql_user, password=options.mysql_password)

rd = redis.StrictRedis(host='localhost', port=6379, db=0)

ids = db.query("select id from fd_People order by id")
for id in ids:
    print id.id
    followers = rd.lrange("u:f:%s"%id.id, 0, -1)
    followers.append(id.id)
    activities = rd.lrange("u:A:%s"%id.id, 0, -1)
    for follower in followers:
        print 'follower:',follower
        for activity in activities:
            print 'activity:',activity
            rd.lpush("my:%s"%follower, activity)
