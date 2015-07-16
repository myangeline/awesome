import hashlib
from aiohttp import web
from conf.config import configs
from www import markdown2
from www.apis import Page, APIValueError
from www.coreweb import get, post
from www.models import *

__author__ = 'sunshine'

COOKIE_NAME = 'awe_session'
_COOKIE_KEY = configs.session.secret


def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        print(e)
    if p < 1:
        p = 1
    return p


def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),
                filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


@get('/')
def index(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findnumber('count(id)')
    page = Page(num, page_index)
    if num == 0:
        summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, ' \
                  'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        blogs = [
            Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
            Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
            Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
        ]
    else:
        blogs = yield from Blog.findall(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }


@get('/blog/{blog_id}')
def get_blog(blog_id):
    blog = yield from Blog.find(blog_id)
    if blog:
        blog.html_content = markdown2.markdown(blog.content)
    else:
        summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, ' \
                  'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        blog = Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120)
        blog.html_content = summary
    print(blog)
    return {
        '__template__': 'blog.html',
        'blog': blog,
    }


@post('/api/authenticate')
def authenticate(*, email, password):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not password:
        raise APIValueError('password', 'Invalid password.')

    users = yield from User.findall('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # 验证密码
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode())
    sha1.update(b':')
    sha1.update(password.encode())
    if user.password != sha1.hexdigest():
        raise APIValueError('password', 'Invalid password.')

    r = web.Response()
    r.set_cookie(COOKIE_NAME, )

