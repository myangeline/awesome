from www import markdown2
from www.apis import Page
from www.coreweb import get
from www.models import *

__author__ = 'sunshine'


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
        blogs = []
    else:
        blogs = yield from Blog.findall(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }


@get('/blog/{id}')
def get_blog(id):
    blog = yield from Blog.find(id)
    comments = yield from Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }
