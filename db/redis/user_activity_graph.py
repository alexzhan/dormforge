from util.getby import get_namedomainuuid_by_id
from util.common import feed_number

class UserActivityGraph(object):

    def __init__(self, client):
        self.client = client
        self.Activity_KEY = 'A'
        self.Sub_Activity_KEYS = ['Follow','Status','Note','Link','Doc']
        self.sub_activity_KEYS = ['follow','status','note','link','doc']

    #Activity_key's format:'u:A:1' ('u:A:user_id')
    
    #Sub_Activity_key's format:'u:Status:1' ('u:Sub_Activity_KEY:user_id')
    #sub_activity_key's format:'status:1:1' ('sub_activity_KEY:user_id:activity_id')
    #because of deletion, sub_activity_key must use max_sub_activity_key + 1

    def add_activity(self, user, actto, acttype, actdict):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        activity_key = self.add_sub_activity(user, actto, acttype, actdict)
        addresult = self.client.lpush(Activity_key, activity_key)
        if acttype in [1,2,3,4]:
            self.client.lpush("all", activity_key)
        self.add_my_activity(user, activity_key)
        return addresult

    def add_my_activity(self, user, activity_key):
        followers = self.client.lrange("u:f:%s" % user, 0, -1)
        followers.append(user)
        for follower in followers:
            key = "my:%s" % follower
            self.client.lpush(key, activity_key)

    def del_activity(self, user, acttype, actto):
        Activity_KEY = 'u:%s:%s' % (self.Activity_KEY, user)
        Activity_key = "u:%s:%s" % (self.Sub_Activity_KEYS[acttype], user)
        activity_key = "%s:%s:%s" % (self.sub_activity_KEYS[acttype], user, actto)
        if acttype == 0:# unfollow somepeople
            if self.client.delete(activity_key):            
                return self.client.lrem(Activity_key, 0, activity_key) and self.client.lrem(Activity_KEY, 0, activity_key) and self.del_my_activity(user, acttype, actto)
            else: return 0
        elif acttype in [1,2,3,4]:# delete status or note or doc
            if self.client.delete(activity_key):
                return self.client.lrem(Activity_key, 0, activity_key) and self.client.lrem(Activity_KEY, 0, activity_key) and self.client.lrem("all", 0, activity_key) and self.del_my_activity(user, acttype, actto)
            else: return 0

    def del_my_activity(self, user, acttype, actto):
        if acttype == 0:
            follow_specific_key = "follow:%s:%s" % (user, actto)
            self.client.lrem("my:%s"%user, 0, follow_specific_key)
            # self del
            for activity_key in self.client.lrange("my:%s"%user, 0, -1):
                act_type,act_user,act_to = activity_key.split(":")
                if act_user == actto:
                    self.client.lrem("my:%s"%user, 0, activity_key)
            # follower del
            followers = self.client.lrange("u:f:%s" % user, 0, -1)
            for follower in followers:
                key = "my:%s" % follower
                self.client.lrem(key, 0, follow_specific_key)
        if acttype in [1,2,3,4]:
            followers = self.client.lrange("u:f:%s" % user, 0, -1)
            followers.append(user)
            for follower in followers:
                key = "my:%s" % follower
                status_key = "%s:%s:%s" % (self.sub_activity_KEYS[acttype], user, actto)
                self.client.lrem(key, 0, status_key)
        return 1

    #acttype:{follow:0;status:1;note:2}
    def add_sub_activity(self, user, actto, acttype, actdict):
        Sub_Activity_key = 'u:%s:%s' % (self.Sub_Activity_KEYS[acttype], user)
        sub_activity_key = '%s:%s:%s' % (self.sub_activity_KEYS[acttype], user, actto)
        self.client.hmset(sub_activity_key, actdict)
        addresult = self.client.lpush(Sub_Activity_key, sub_activity_key)
        return sub_activity_key

    def get_top_activities(self, user, db, isself, startindex, item_num):
        Activity_list = []
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        All_Activity_list = self.client.lrange(Activity_key, startindex, -1)
        index = 0
        for sub_activity_key in All_Activity_list:
            acttype,actuser,actto = sub_activity_key.split(":")
            if acttype == 'follow':
                sub_activity = self.client.hmget(sub_activity_key, ["time",])
                username,domain,uuid = get_namedomainuuid_by_id(db, self.client, actto)
                sub_activity.append(username)#follow who
                sub_activity.append(domain)#domain
                sub_activity.append(actto)#actto id
                sub_activity.append(uuid)#actto uuid
                sub_activity.append(0)#type:0
            elif acttype == 'status':
                sub_activity = self.client.hmget(sub_activity_key, ["time","status"])
                sub_activity.append(actto)#actto
                sub_activity.append(1)#type:1
            elif acttype == 'note':
                sub_activity = self.client.hmget(sub_activity_key, ["time","title","content","status"])
                if not isself and sub_activity[3] != '0':
                    continue
                sub_activity.append(actto)#actto
                sub_activity.append(2)#type:2
            elif acttype == 'link':
                sub_activity = self.client.hmget(sub_activity_key, ["time","url","title","status"])
                if not isself and sub_activity[3] != '0':
                    continue
                sub_activity.append(actto)#actto
                sub_activity.append(3)#type:3
            elif acttype == 'doc':
                sub_activity = self.client.hmget(sub_activity_key, ["time","docid","title","status"])
                if not isself and sub_activity[3] != '0':
                    continue
                sub_activity.append(actto)#actto
                sub_activity.append(4)#type:4
            Activity_list.append(sub_activity)                    
            index = index + 1
            if index == item_num:
                break
        return Activity_list

    def get_top_sub_activities(self, user, acttype, isself, startindex, item_num):
        Sub_Activity_list = []
        Sub_Activity_key = "u:%s:%s" % (self.Sub_Activity_KEYS[acttype], user)
        index = 0
        for sub_activity_key in self.client.lrange(Sub_Activity_key, startindex, -1):
            actto = sub_activity_key.split(":")[-1]
            if acttype == 1:
                sub_activity = self.client.hmget(sub_activity_key, ["time",'status'])
                sub_activity.append(actto)
                sub_activity.append(1)
            if acttype == 2:
                sub_activity = self.client.hmget(sub_activity_key, ["time","title","content","status"])
                if not isself and sub_activity[3] != '0':
                    continue
                sub_activity.append(actto)
                sub_activity.append(2)
            if acttype == 3:
                sub_activity = self.client.hmget(sub_activity_key, ["time","url","title","status"])
                if not isself and sub_activity[3] != '0':
                    continue
                sub_activity.append(actto)
                sub_activity.append(3)
            if acttype == 4:
                sub_activity = self.client.hmget(sub_activity_key, ["time","docid","title","status"])
                if not isself and sub_activity[3] != '0':
                    continue
                sub_activity.append(actto)
                sub_activity.append(4)
            Sub_Activity_list.append(sub_activity)
            index = index + 1
            if index == item_num:
                break
        return Sub_Activity_list

    #whole-site activities
    def get_all_activities(self, db, startindex, ispoll):
        all_activities = []
        startindex = 0 if ispoll else startindex
        lastindex = ispoll-1 if ispoll else startindex+feed_number-1
        activities_list = self.client.lrange("all", startindex, lastindex)
        index = startindex + 1
        for activity in activities_list:
            acttype, act_userid, actto = activity.split(":")
            act_username,act_domain,act_uuid = get_namedomainuuid_by_id(db, self.client, act_userid)
            if acttype == 'status':
                real_activity = self.client.hmget(activity, ["time",'status','comm'])
            elif acttype == 'note':
                real_activity = self.client.hmget(activity, ["time","title","content","status",'comm'])
            elif acttype == 'link':
                real_activity = self.client.hmget(activity, ["time","url","title","summary",'status','comm'])
            elif acttype == 'doc':
                real_activity = self.client.hmget(activity, ["time","docid","title","summary",'status','comm'])
            real_activity.append(actto)
            real_activity.append(act_userid)
            real_activity.append(act_username)
            real_activity.append(act_domain)
            real_activity.append(act_uuid)
            real_activity.append(acttype)
            real_activity.append(index)
            index = index + 1
            all_activities.append(real_activity)
        return all_activities

    #my following activities
    def get_my_activities(self, db, user, startindex):
        my_activities = []
        activities_list = self.client.lrange("my:%s"%user, startindex, startindex+feed_number-1)
        index = startindex + 1
        for activity in activities_list:
            acttype, act_userid, actto = activity.split(":")
            act_username,act_domain,act_uuid = get_namedomainuuid_by_id(db, self.client, act_userid)
            if acttype == 'status':
                real_activity = self.client.hmget(activity, ["time",'status','comm'])
                real_activity.append(actto)
            if acttype == 'note':
                real_activity = self.client.hmget(activity, ["time","title","content","status",'comm'])
                real_activity.append(actto)
            elif acttype == 'link':
                real_activity = self.client.hmget(activity, ["time","url","title","summary",'status','comm'])
                real_activity.append(actto)
            elif acttype == 'doc':
                real_activity = self.client.hmget(activity, ["time","docid","title","summary",'status','comm'])
                real_activity.append(actto)
            if acttype == 'follow':
                actto_username,actto_domain,actto_uuid = get_namedomainuuid_by_id(db, self.client, actto)
                real_activity = self.client.hmget(activity, ["time",])
                real_activity.append(actto)
                real_activity.append(actto_username)
                real_activity.append(actto_domain)
                real_activity.append(actto_uuid)
            real_activity.append(act_userid)
            real_activity.append(act_username)
            real_activity.append(act_domain)
            real_activity.append(act_uuid)
            real_activity.append(acttype)
            real_activity.append(index)
            index = index + 1
            my_activities.append(real_activity)
        return my_activities

    def count_activity(self, user):
        Activity_key = 'u:%s:%s' % (self.Activity_KEY, user)
        return self.client.llen(Activity_key)

    def count_sub_activity(self, user, acttype):
        Sub_Activity_key = 'u:%s:%s' % (self.Sub_Activity_KEYS[acttype], user)
        return self.client.llen(Sub_Activity_key)

    def count_all_activity(self):
        return self.client.llen("all")

    def count_my_activity(self, user):
        return self.client.llen("my:%s" % user)
