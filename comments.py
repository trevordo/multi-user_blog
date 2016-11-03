
class CommentDetails(BlogHandler):
    def get(self, comment_id):
        key = db.Key.from_path('comment', int(comment_id), parent=blog_key())
        comment = db.get(key)

        if not comment:
            self.error(404)
            return

        self.render("permalink.html", comment = comment)

class NewComment(BlogHandler):
    def get(self):
        if self.user:
            self.render("newcomment.html")
        else:
            self.redirect("/login")

    def comment(self):
        if not self.user:
            self.redirect('/blog')

        subject = self.request.get('subject')
        content = self.request.get('content')
        author = str(self.user.name)

        if subject and content:
            p = comment(parent = blog_key(),
                     subject = subject,
                     content = content,
                     author = author)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newcomment.html",
                        subject=subject, 
                        content=content, 
                        error=error)

class EditComment(BlogHandler):
    def get(self):
        if self.user:
            comment_id = self.request.get("comment")
            key = db.Key.from_path('comment', int(comment_id), parent=blog_key())
            comment = db.get(key)
            subject = comment.subject
            content = comment.content

            self.render("editcomment.html", subject=subject, content=content)
        else:
            self.redirect("/login")

    def comment(self):
        if not self.user:
            self.redirect('/blog')

        comment_id = self.request.get("comment")
        key = db.Key.from_path('comment', int(comment_id), parent=blog_key())
        comment = db.get(key)
        subject = self.request.get('subject')
        content = self.request.get('content')
        
        if subject and content:
            comment.subject = subject
            comment.content = content
            comment.put()
            self.redirect('/blog/%s' % str(comment.key().id()))
            
        else:
            error = "subject and content are required, please!"
            self.render("editcomment.html",
                        subject=subject, 
                        content=content, 
                        error=error)

class DeleteComment(BlogHandler):
    def get(self):
        if self.user:
            comment_id = self.request.get("comment")
            key = db.Key.from_path('comment', int(comment_id), parent=blog_key())
            comment = db.get(key)

            self.render("deletecomment.html", comment=comment)
        else:
            self.redirect("/login")

    def comment(self):
        if not self.user:
            self.redirect('/blog')

        else: 
            comment_id = self.request.get("comment")
            key = db.Key.from_path("comment", int(comment_id), parent=blog_key())
            comment = db.get(key)
            
            if comment and comment.author == self.user.name:
                comment.delete()
                self.redirect('/blog')
            else:
                error = "comment can only be deleted by author!"
                self.render("deletecomment.html",
                            subject=subject, 
                            content=content, 
                            error=error)

