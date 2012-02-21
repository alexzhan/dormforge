def get_namedomain_by_id(db, client, userid):
    if client.hmget('u:' + userid, ['name','domain'])[0]:
        return client.hmget('u:' + userid, ['name','domain'])
    else:
        userinfo = db.get("select name,domain from fd_People where id = %s", userid)
        client.hmset('u:' + userid, {"name":userinfo.name,"domain":userinfo.domain})
        return [userinfo.name, userinfo.domain]
