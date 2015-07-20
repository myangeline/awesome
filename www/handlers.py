import asyncio
import hashlib
import logging
from aiohttp import web
import json
import datetime
from conf.config import configs
from www import markdown2
from www.apis import Page, APIValueError, APIPermissionError
from www.coreweb import get, post
from www.models import *
from www.util.handlerutil import user2cookie, JSONEncoder

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


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


@get('/')
def index():
    blogs = yield from Blog.findall(orderBy='created_at desc')
    category = yield from Category.findall(orderBy='id desc')
    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        'category': category
    }


@get('/category/{category_id}')
def get_blogs_by_category(category_id):
    blogs = yield from Blog.findall(where="category='" + category_id + "'")
    category = yield from Category.findall(orderBy='id desc')
    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        'category': category
    }


@get('/blog/{blog_id}')
def get_blog(blog_id):
    blog = yield from Blog.find(blog_id)
    if blog:
        blog.html_content = markdown2.markdown(blog.content)
    else:
        summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, ' \
                  'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        blog = Blog(id='1', name='Test Blog', summary=summary, created_at=time.time() - 120)
        blog.html_content = summary
    return {
        '__template__': 'blog.html',
        'blog': blog,
    }


@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
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
    if user.password != password:
        raise APIValueError('password', 'Invalid password.')

    # 验证通过
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400, _COOKIE_KEY),
                 max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps({'user': user, 'status': 'ok'}, ensure_ascii=False, cls=JSONEncoder).encode()
    return r


@get('/manage/')
def manage(request):
    return 'redirect:/manage/blogs'


@get('/manage/blogs')
def manage_blogs(request, *, page='1'):
    check_admin(request)
    blogs = yield from Blog.findall(orderBy='created_at desc')

    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page),
        'blogs': blogs
    }


@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


@get('/manage/blogs/edit')
def manage_edit_blog(*, blog_id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': blog_id,
        'action': '/api/blogs/%s' % blog_id
    }


@get('/api/blogs')
def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findnumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = yield from Blog.findall(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


@get('/api/blogs/{id}')
def api_get_blog(request, *, id):
    check_admin(request)
    blog = yield from Blog.find(id)
    return json.dumps({'status': 'ok', 'blog': blog}, cls=JSONEncoder)


@post('/api/blogs')
def api_create_blog(request, *, name, summary, content, category):
    check_admin(request)
    try:
        if not name or not name.strip():
            raise APIValueError('name', 'name cannot be empty.')
        if not summary or not summary.strip():
            raise APIValueError('summary', 'summary cannot be empty.')
        if not content or not content.strip():
            raise APIValueError('content', 'content cannot be empty.')
        blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image,
                    name=name.strip(), summary=summary.strip(), content=content.strip(),
                    category=category.strip(), created_at=datetime.datetime.now())
        yield from blog.save()
    except BaseException as e:
        print(e)
        return json.dumps({'status': 'error', 'msg': '日志保存失败！'})
    return json.dumps({'status': 'ok', 'msg': '日志保存成功！'})


@post('/api/blogs/{id}')
def api_update_blog(id, request, *, name, summary, content, category):
    check_admin(request)
    try:
        blog = yield from Blog.find(id)
        if not name or not name.strip():
            raise APIValueError('name', 'name cannot be empty.')
        if not summary or not summary.strip():
            raise APIValueError('summary', 'summary cannot be empty.')
        if not content or not content.strip():
            raise APIValueError('content', 'content cannot be empty.')
        blog.name = name.strip()
        blog.summary = summary.strip()
        blog.content = content.strip()
        blog.category = category.strip()
        yield from blog.update()
    except BaseException as e:
        print(e)
        return json.dumps({'status': 'error', 'msg': '日志更新失败！'})
    return json.dumps({'status': 'ok', 'msg': '日志更新成功！'})


@post('/api/blogs/delete')
def api_delete_blog(request, *, id):
    check_admin(request)
    try:
        blog = yield from Blog.find(id)
        yield from blog.remove()
    except BaseException as e:
        print(e)
        return json.dumps({'status': 'error', 'msg': '日志删除失败！'})
    return json.dumps({'status': 'ok', 'msg': '日志删除成功！'})


@get('/manage/category')
def manage_category():
    category = yield from Category.findall(orderBy='id desc')
    return {
        '__template__': 'manage_category.html',
        'category': category,
    }


@post('/api/category/add')
def api_add_category(request, *, name):
    check_admin(request)
    try:
        if not name:
            raise APIValueError('name', 'category name cannot be empty.')
        category = Category(name=name, user_id=request.__user__.id)
        # category = Category(name=name, user_id='a1001')
        yield from category.save()
    except BaseException as e:
        print(e)
        return json.dumps({'status': 'error'})
    return json.dumps({'status': 'ok'})


@post('/api/category/update')
def api_update_category(request, *, category_id, name):
    check_admin(request)
    try:
        if not name:
            raise APIValueError('name', 'category name cannot be empty.')
        if not category_id:
            raise APIValueError('category_id', 'category id cannot be empty.')
        category = yield from Category.find(category_id)
        if category:
            category.name = name
            yield from category.update()
        else:
            return json.dumps({'status': 'error', 'msg': '分类不存在'})
    except BaseException as e:
        print(e)
        return json.dumps({'status': 'error', 'msg': '分类更新失败'})
    return json.dumps({'status': 'ok', 'msg': '分类更新成功'})


@post('/api/category/delete')
def api_delete_category(request, *, category_id):
    check_admin(request)
    try:
        if not category_id:
            raise APIValueError('category_id', 'category id cannot be empty.')
        category = Category(id=category_id)
        yield from category.remove()
    except BaseException as e:
        print(e)
        return json.dumps({'status': 'error', 'msg': '分类删除失败'})
    return json.dumps({'status': 'ok', 'msg': '分类删除成功'})


@get('/api/category/get')
def api_get_category():
    category = yield from Category.findall(orderBy='id desc')
    return json.dumps({'category': category})