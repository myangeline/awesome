import hashlib
import time

__author__ = 'sunshine'


def user2cookie(user, max_age, cookie_key):
    """
    计算加密cookie
    :param user:
    :param max_age:
    :param cookie_key:
    :return:
    """
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, cookie_key)
    l = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(l)