class BlogComment(BlogHandler):
    def get(self):
        posts = greetings = Post.all().order('-created')
        self.render('front.html', posts = posts)

class PostComment(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewComment(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/blog')

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

class EditComment(BlogHandler):
    def get(self):
        if self.user:
            post_id = self.request.get("post")
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            subject = post.subject
            content = post.content

            self.render("editpost.html", subject=subject, content=content)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/blog')

        post_id = self.request.get("post")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        subject = self.request.get('subject')
        content = self.request.get('content')
        
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

class DeleteComment(BlogHandler):
    def get(self):
        if self.user:
            post_id = self.request.get("post")
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            self.render("deletepost.html", post=post)
        else:
            self.redirect("/login")

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

class DetailsComment(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("details.html", post = post)