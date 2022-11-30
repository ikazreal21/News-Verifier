from django.db import models

# Create your models here

class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    excerpt = models.TextField()
    url = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    news_site_url = models.CharField(max_length=255)
    dtstr = models.CharField(max_length=50, default='None')

    def __str__(self):
        return self.title