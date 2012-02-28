from db.redis.user_activity_graph import UserActivityGraph

def add_activity(client, actuser, actto, acttype, actdict):
    uag = UserActivityGraph(client)
    return uag.add_activity(actuser, actto, acttype, actdict)

def del_activity(client, actuser ,acttype, actto):
    uag = UserActivityGraph(client)
    return uag.del_activity(actuser, acttype, actto)
