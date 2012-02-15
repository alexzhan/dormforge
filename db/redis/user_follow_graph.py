class UserFollowGraph(object):

    def __init__(self, client):
        self.client = client

        self.FOLLOWS_KEY = 'F'
        self.FOLLOWERS_KEY = 'f'
        self.BLOCKS_KEY = 'B'
        self.BLOCKED_KEY = 'b'

    #forward_key' format : 'u:F:1' ('u:F:user_id')
    #reverse_key' format : 'u:f:1' ('u:f:user_id')
    def follow(self, from_user, to_user):
        if to_user in self.get_follows(from_user):
            return False
        forward_key = 'u:%s:%s' % (self.FOLLOWS_KEY, from_user)
        forward = self.client.lpush(forward_key, to_user)
        reverse_key = 'u:%s:%s' % (self.FOLLOWERS_KEY, to_user)
        reverse = self.client.lpush(reverse_key, from_user)
        return forward and reverse

    def unfollow(self, from_user, to_user):
        if to_user not in self.get_follows(from_user):
            return False
        forward_key = 'u:%s:%s' % (self.FOLLOWS_KEY, from_user)
        forward = self.client.lrem(forward_key, 0, to_user)
        reverse_key = 'u:%s:%s' % (self.FOLLOWERS_KEY, to_user)
        reverse = self.client.lrem(reverse_key, 0, from_user)
        return forward and reverse

    def get_follows(self, user):
        return list(self.client.lrange('u:%s:%s' % (self.FOLLOWS_KEY, user), 0, -1))

    def get_followers(self, user):
        return list(self.client.lrange('u:%s:%s' % (self.FOLLOWERS_KEY, user), 0, -1))

    def is_follow(self, user_a, user_b):
        return str(user_b) in self.get_follows(user_a)

    def is_follower(self, user_a, user_b):
        return str(user_b) in self.get_followers(user_a)

    def is_mutual(self, user_a, user_b):
        return self.is_follow(user_a, user_b) and self.is_follower(user_a, user_b)

    def follow_count(self, user):
        return self.client.llen('u:%s:%s' % (self.FOLLOWS_KEY, user))

    def follower_count(self, user):
        return self.client.llen('u:%s:%s' % (self.FOLLOWERS_KEY, user))

    def common_follow(self, user_a, user_b):
        follows_a = self.get_follows(user_a)
        follows_b = self.get_follows(user_b)
        return list(set(follows_a).intersection(set(follows_b)))

    def common_follower(self, user_a, user_b):
        followers_a = self.get_followers(user_a)
        followers_b = self.get_followers(user_b)
        return list(set(followers_a).intersection(set(followers_b)))
