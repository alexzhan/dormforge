def get_namedomain_by_id(db, client, userid):
    if client.hmget('u:' + userid, ['name','domain'])[0]:
        return client.hmget('u:' + userid, ['name','domain'])
    else:
        userinfo = db.get("select name,domain from fd_People where id = %s", userid)
        client.hmset('u:' + userid, {"name":userinfo.name,"domain":userinfo.domain})
        return [userinfo.name, userinfo.domain]

def get_domain_by_name(db, client, username):
    if client.get("u:name:%s" % username):
        return client.get("u:name:%s" % username)
    else:
        domain = db.get("select domain from fd_People where name = %s", username)
        if domain:
            domain = domain.domain
            client.set("u:name:%s" % username, domain)
        return domain
