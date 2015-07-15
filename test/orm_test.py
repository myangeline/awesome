from www.models import User

__author__ = 'sunshine'


def test_user():
    user = User(
        email='269614597@qq.com',
        password='admin',
        admin=True,
        name='龙骑士',
    )
    user.save()

# test_user()

from collections import deque
import itertools
itertools.permutations