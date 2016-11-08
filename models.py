from google.appengine.ext import db

class Comment(db.Model):
    """
    Class db model for Comment using Google datastore
    Returns:
        return render of comments.html with comments property names
    """

    # continue with property names
    post_key = db.StringProperty(required = True)
    author = db.StringProperty(required = False)
    comment = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.comment.replace('\n', '<br>')
        return render_str("comment.html", c = self)

class Post(db.Model):
        """
    Class db model for Post using Google datastore
    Returns:
        return render of post.html with property names
    """

    # continue with property names
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