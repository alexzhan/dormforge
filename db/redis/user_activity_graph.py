class UserActivityGraph(object):

    def __init__(self, client):
        self.client = client
        self.Activity_KEY = 'A'
        self.activity_KEY = 'a'

    #Activity_key's format:'u:A:1' ('u:A:user_id')
    #activity_key's format:'a:1:1' ('a:user_id:activity_id')
    #because of deletion, activity_key's must use max_activity_id + 1
    def add_activity(self, user, actdict):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        max_activity = self.client.lindex(Activity_key, -1)
        if not max_activity:
            max_activity = 0
        else:
            max_activity = int(max_activity.split(":")[-1])
        activity_key = '%s:%s:%s' % (self.activity_KEY, user, max_activity + 1)
        self.client.hmset(activity_key, actdict)
        addresult = self.client.lpush(Activity_key, activity_key)
        return addresult

    def del_activity(self, user, actto):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        activity_key = '%s:%s:%s' % (self.activity_KEY, user, self.client.llen(Activity_key) + 1)
        for activity_key in self.client.lrange(Activity_key, 0, -1):
            if self.client.hmget(activity_key, ['to'])[0] == actto:
                #here we don't hmdel the activity,because:1,there is no hmdel command for now
                #in redis2.9.3 and there is no need to del it if your memory is enough
                break
        return self.client.lrem(Activity_key, 0, activity_key)

    #get top 5 activities
    def get_top_activities(self, user):
        Activity_list = []
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        for i in range(5):
            if self.client.lindex(Activity_key, i):
                Activity_list.append(self.client.hmget(self.client.lindex(Activity_key, i), ["type","time","to"]))
        return Activity_list

    def count_activity(self, user):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        return self.client.llen(Activity_key)
