from django.db import models
from django.contrib.auth.models import User

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Blog(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blogs")
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    def __str__(self):
        return self.title

class Like(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="likes")
    
    class Meta:
        unique_together = ('user', 'blog')

class Comment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    
    def __str__(self):
        return self.content
