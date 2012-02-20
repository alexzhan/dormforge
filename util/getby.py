def get_username_by_id(db, client, userid):
    if client.get('u:' + userid):
        username = client.get('u:' + userid)
    else:
        username = db.get("select name from fd_People where id = %s", userid).name
        client.set('u:' + userid, username)
    return username
