class UserActivityGraph(object):

    def __init__(self, client):
        self.client = client
        self.Activity_KEY = 'A'
        self.Sub_Activity_KEYS = ['Follow','Status']
        self.sub_activity_KEYS = ['follow','status']

    #Activity_key's format:'u:A:1' ('u:A:user_id')
    
    #Sub_Activity_key's format:'u:Status:1' ('u:Sub_Activity_KEY:user_id')
    #sub_activity_key's format:'status:1:1' ('sub_activity_KEY:user_id:activity_id')
    #because of deletion, sub_activity_key must use max_sub_activity_key + 1

    def add_activity(self, user, acttype, actdict):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        activity_key = self.add_sub_activity(user, acttype, actdict)
        addresult = self.client.lpush(Activity_key, activity_key)
        if acttype == 1:
            self.client.lpush("all", activity_key)
        return addresult

    def del_activity(self, user, acttype, actto):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        mark = 1
        if acttype == 0:
            for activity_key in self.client.lrange(Activity_key, 0, -1):
                if self.client.hmget(activity_key, ['to'])[0] == actto:
                    #here 1,we don't hmdel the activity,because:there is no hmdel command for now
                    #in redis2.9.3 and there is no need to del it if your memory is enough
                    #2,we must put a mark here because there may not exist the key we want to del,
                    #but without a mark,we have to del the largest key as the loop goes
                    mark = 0
                    break
            if mark:
                return False
            else:
                return self.client.lrem(Activity_key, 0, activity_key)
        elif acttype == 1:
            Status_key = 'u:Status:%s' % user
            for status_key in self.client.lrange(Status_key, 0, -1):
                if self.client.hmget(status_key, ['to'])[0] == actto:
                    mark = 0
                    break
            if mark:
                return False
            else:
                return self.client.lrem(Status_key, 0, status_key) and self.client.lrem(Activity_key, 0, status_key) and self.client.lrem("all", 0, status_key)

    #acttype:{follow:0;status:1}
    def add_sub_activity(self, user, acttype, actdict):
        Sub_Activity_key = 'u:%s:%s' % (self.Sub_Activity_KEYS[acttype], user)
        max_activity = self.client.lindex(Sub_Activity_key, 0)
        if not max_activity:
            max_activity = 0
        else:
            max_activity = int(max_activity.split(":")[-1])
        sub_activity_key = '%s:%s:%s' % (self.sub_activity_KEYS[acttype], user, max_activity + 1)
        self.client.hmset(sub_activity_key, actdict)
        addresult = self.client.lpush(Sub_Activity_key, sub_activity_key)
        return sub_activity_key

    #get top 5 activities
    def get_top_activities(self, user):
        Activity_list = []
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        for i in range(5):
            sub_activity_key = self.client.lindex(Activity_key, i)
            if sub_activity_key:
                if sub_activity_key.split(":")[0] == 'follow':
                    sub_activity = self.client.hmget(sub_activity_key, ["time","to"])
                    sub_activity.append(0)#type:0
                    Activity_list.append(sub_activity)                    
                elif sub_activity_key.split(":")[0] == 'status':
                    sub_activity = self.client.hmget(sub_activity_key, ["time","to",'status'])
                    sub_activity.append(1)#type:1
                    Activity_list.append(sub_activity)                    
        return Activity_list

    #get top 3 sub_activities
    def get_top_sub_activities(self, user, acttype):
        Sub_Activity_list = []
        Sub_Activity_key = "u:%s:%s" % (self.Sub_Activity_KEYS[acttype], user)
        for i in range(3):
            sub_activity_key = self.client.lindex(Sub_Activity_key, i)
            if sub_activity_key:
                if acttype == 1:
                    sub_activity = self.client.hmget(sub_activity_key, ["time","to",'status'])
                    Sub_Activity_list.append(sub_activity)
        return Sub_Activity_list

    #whole-site activities
    def get_all_activities(self, db):
        all_activities = []
        activities_list = self.client.lrange("all", 0, -1)
        index = 1
        for activity in activities_list:
            acttype = activity.split(":")[0]
            act_userid = activity.split(":")[1]
            if self.client.get('u:' + act_userid):
                act_username = self.client.get('u:' + act_userid)
            else:
                act_username = db.get("select name from fd_People where id = %s", act_userid).name
                self.client.set('u:' + act_userid, act_username)
            if acttype == 'status':
                real_activity = self.client.hmget(activity, ["time","to",'status'])
                real_activity.append(act_username)
                real_activity.append(acttype)
                real_activity.append(index)
            index = index + 1
            all_activities.append(real_activity)
        return all_activities

    def count_activity(self, user):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        return self.client.llen(Activity_key)

    def count_sub_activity(self, user, acttype):
        Sub_Activity_key = 'u:%s:%s' % (self.Sub_Activity_KEYS[acttype], user)
        return self.client.llen(Sub_Activity_key)
