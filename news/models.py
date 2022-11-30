from django.db import models

# Create your models here.

class Phrase(models.Model):
    searchPhrase = models.CharField(max_length=255)

    def __str__(self):
        return self.searchPhrase

class News(models.Model):
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    excerpt = models.TextField()
    url = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    news_site_url = models.CharField(max_length=255)

    def __str__(self):
        return self.title