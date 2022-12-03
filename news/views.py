from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import get_date_difference

from .models import *
from .forms import *


from newscatcherapi import NewsCatcherApiClient
from django.db.models import Q
import datetime

newscatcherapi = NewsCatcherApiClient(
    x_api_key="_fAzEqugadhAfLLIzLtNsXz9-HfVw5HFIUUEu1Ao3ck"
    # x_api_key="g8EYZLLr3R6q7sBhuK6LWPDlPVV3T86WsZAo0v2NYt8"
)


def get_news_api(message):

    query = f"{message}"
    news_article = newscatcherapi.get_search(
        q=query,
        lang="en,tl",
        countries="PH",
        sources="cnnphilippines.com,philstar.com,manilatimes.net,mb.com.ph,\
        tv5.com.ph,inquirer.net,dzrh.com.ph,abs-cbn.com,gmanetwork.com",
        page_size=50,
    )

    article_arr = []
    if news_article["page_size"] != 0:
        for data in news_article["articles"]:
            articles = {}
            articles["title"] = data["title"]
            articles["content"] = data["summary"]
            articles["excerpt"] = data["excerpt"]
            articles["author"] = data["author"]
            articles["news_site_url"] = data["clean_url"]
            articles["url"] = data["link"]
            articles["dtstr"] = data["published_date"]
            article_arr.append(articles)
    print(article_arr)
    return article_arr


def save_news_to_database(articles):
    for article in articles:
        news = News()
        news.title = article["title"]
        news.content = article["content"]
        news.excerpt = article["excerpt"]
        news.news_site_url = article["news_site_url"]
        news.author = article["author"]
        news.url = article["url"]
        news.dtstr = article["dtstr"]
        news.save()


def index(request):
    pred = ""
    news = ""
    message = ""
    try:
        if request.method == "POST":
            message = request.POST.get("message")
            print("message1", message)
            existing = News.objects.filter(
                Q(title__icontains=message)
                | Q(content__icontains=message)
                | Q(excerpt__icontains=message)
            )
            print(existing.count())
            if existing.count() != 0:
                news = existing
                print("if")
            else:
                news = get_news_api(message)
                if len(news) != 0:
                    save_news_to_database(news)
    except:
        pred = "Error"

    context = {
        "predict": "Verified"
        if news
        else "Unverified"
        if not news and message
        else pred,
        "news": [
            {
                **(d.__dict__ if not isinstance(d, dict) else d),
                "dtstr": get_date_difference(getattr(d, "dtstr")),
            }
            for d in news
            if d
        ],
        "search_term": message,
    }
    print("CONTEXT=", context)
    return render(request, "news/index.html", context)
