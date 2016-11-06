import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'I_@m_the_master_0f_N0p3!'

##### Template rendering from jinja2

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

##### cookie validation

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

##### user login

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

##### blog code

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

### Database Models for Comment and Post
class Post(db.Model):
    author = db.StringProperty(required = False)
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    likes = db.IntegerProperty(required=False, default = 0)
    liked_by = db.ListProperty(str)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class Comment(db.Model):
    post_key = db.StringProperty(required = True)
    author = db.StringProperty(required = False)
    comment = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.comment.replace('\n', '<br>')
        return render_str("comment.html", c = self)

##### Blog section rendering and post manipulation

class BlogFront(BlogHandler):
    def get(self):
        posts = greetings = Post.all().order('-created')
        self.render('front.html', posts = posts)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')

        subject = self.request.get('subject')
        content = self.request.get('content')
        author = str(self.user.name)

        if subject and content:
            p = Post(parent = blog_key(),
                     subject = subject,
                     content = content,
                     author = author)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        subject=subject,
                        content=content,
                        error=error)

class EditPost(BlogHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")  

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        subject = post.subject
        content = post.content

        if not post:
            self.error(404)
            return

        else:
            self.render("editpost.html", subject=subject, content=content)
          
        
        if post and post.author != self.user.name:
            error = "You are not the author."
            self.redirect('error.html', error=error)

    def post(self):
        if not self.user:
            self.redirect('/login')

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        subject = self.request.get('subject')
        content = self.request.get('content')

        if post and post.author != self.user.name:
            error = "You are not the author."
            self.redirect('error.html', error=error)

        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))

        else:
            error = "subject and content are required, please!"
            self.render("editpost.html",
                        subject=subject,
                        content=content,
                        error=error)

class DeletePost(BlogHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")
            
        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        else:
            self.render("deletepost.html", post=post)    

        if post and post.author != self.user.name:
            error = "You are not the author."
            self.redirect('error.html', error=error)

    def post(self):
        if not self.user:
            self.redirect('/blog')

        else:
            post_id = self.request.get("post")
            key = db.Key.from_path("Post", int(post_id), parent=blog_key())
            post = db.get(key)

            if post and post.author == self.user.name:
                post.delete()
                self.redirect('/blog')
            else:
                error = "Post can only be deleted by author!"
                self.render("deletepost.html",
                            subject=subject,
                            content=content,
                            error=error)

##### Comment section rendering and comment manipulation

class DetailsPage(BlogHandler):
    def get(self):
        # get post
        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        comments = db.Query(Comment).filter('post_key',
                                            post_id).order('-created')

        if not post:
            self.error(404)
            return

        self.render("details.html",
                     post = post,
                     comments = comments)

    def post(self):
        if not self.user:
            self.redirect('/login')

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        post_key = str(post.key().id())
        comment = self.request.get('comment')
        author = str(self.user.name)

        if comment:
            c = Comment(parent = blog_key(),
                        post_key = post_key,
                        comment = comment,
                        author = author)
            c.put()
            self.redirect('/blog/details?post=%s' % str(post.key().id()))
        else:
            comments = db.Query(Comment).filter('post_key',
                                                post_id).order('-created')
            error = "Please enter a comment."
            self.render("details.html",
                        post = post,
                        comment=comment,
                        comments=comments,
                        error=error)

class EditComment(BlogHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        comment_id = self.request.get("comment")
        key = db.Key.from_path('Comment',
                                int(comment_id),
                                parent=blog_key())
        q = db.get(key)

        comment = q.comment

        if not post:
            self.error(404)
            return

        else:
            self.render("editcomment.html", content=comment, q=q)

        if q and q.author != self.user.name:
            error = "You are not the author."
            self.redirect('error.html', error=error)

    def post(self):
        if not self.user:
            self.redirect('/blog')

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        comment_id = self.request.get("comment")
        key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
        c = db.get(key)
        comment = self.request.get('content')

        if c and c.author != self.user.name:
            error = "You are not the author."
            self.redirect('error.html', error=error)

        if comment:
            c.comment = comment
            c.put()
            self.redirect('/blog/details?post=%s' % str(post.key().id()))

        else:
            error = "Please enter a comment!"
            self.render("editcomment.html",
                        comment=comment,
                        error=error)
                        
class DeleteComment(BlogHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        comment_id = self.request.get("comment")
        key = db.Key.from_path('Comment',
                                int(comment_id),
                                parent=blog_key())
        q = db.get(key)

        if not post:
            self.error(404)
            return

        else:
            self.render("deletecomment.html", comments=q)
        
        if q and q.author != self.user.name:
            error = "You are not the author."
            self.redirect('error.html', error=error)

    def post(self):
        if not self.user:
            self.redirect('/blog')

        else:
            post_id = self.request.get("post")
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            comment_id = self.request.get("comment")
            key = db.Key.from_path('Comment',
                                    int(comment_id),
                                    parent=blog_key())
            q = db.get(key)

            if q and q.author == self.user.name:
                q.delete()
                self.redirect('/blog/details?post=%s' % str(post.key().id()))
            else:
                error = "comment can only be deleted by author!"
                self.render("deletecomment.html",
                            comments=q,
                            error=error)

##### Likes section rendering

class LikePost(BlogHandler):
    def get(self):
        if not self.user:
            self.redirect('/blog')

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        current_user = self.user.name
        author = post.author

        if not self.user:
            self.redirect('/login')
        elif current_user in post.liked_by:
            error = "You already liked this post"
            self.render("error.html", error=error)
        else:    
            post.likes += int(1)
            post.liked_by.append(current_user)
            post.put()
            self.redirect("/blog")

class UnlikePost(BlogHandler):
    def get(self):
        if not self.user:
            self.redirect('/blog')

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        current_user = self.user.name
        author = post.author

        if not self.user:
            self.redirect('/login')
        elif current_user not in post.liked_by:
            error = "You have not yet liked this post"
            self.render("error.html", error=error)
        else:
            post.likes -= int(1)
            post.liked_by.remove(current_user)
            post.put()
            self.redirect("/blog")

##### Form validation

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

##### registration and login/logout

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/blog')

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')

##### page redirects

class MainPage(BlogHandler):
  def get(self):
      self.redirect('/blog')

class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/details', DetailsPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/editpost', EditPost),
                               ('/blog/deletepost', DeletePost),
                               ('/blog/editcomment', EditComment),
                               ('/blog/deletecomment', DeleteComment),
                               ('/blog/likepost', LikePost),
                               ('/blog/unlikepost', UnlikePost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
                               ],
                              debug=True)
