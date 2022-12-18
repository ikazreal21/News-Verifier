from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import get_date_difference

from .models import *
from .forms import *

# for testing
# from .daily_news import daily_news


from newscatcherapi import NewsCatcherApiClient
from django.db.models import Q
import datetime

newscatcherapi = NewsCatcherApiClient(
    # x_api_key="L2QU2I1Nm5xpHRIjAccgbfSMR_l6VUrxhiVI1Av8zMk"
    # this is for defense day (researcher's side)
    x_api_key="gtf2nNX5XIU5n_SW3TLgZ6gODv6MDUYXM_e9KYJgtv4"
    # this is for defense day (panel side)
    # x_api_key="1JuDVL2WGmKMlf6eClndPIj1h6dXIDkT0o6XYfMTZxY"
)



# def check_expired_data():
#     News.objects.filter(
#         posting_date__lte=datetime.now() - timedelta(minutes=1)
#     ).delete()
#     print("deleted")


def arrange_news(news_article, daily_news=0):
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
            if daily_news == 1:
                articles["media"] = data["media"]
            else:
                articles["media"] = None
            articles["dtstr"] = data["published_date"]
            article_arr.append(articles)
    print(article_arr)
    return article_arr

def get_news_api(message):

    query = f"{message}"
    news_article = newscatcherapi.get_search(
        q=f'"{query}"',
        lang="en,tl",
        countries="PH",
        sources="cnnphilippines.com,philstar.com,manilatimes.net,mb.com.ph,\
            news.tv5.com.ph,inquirer.net,dzrh.com.ph,abs-cbn.com,gmanetwork.com,bomboradyo.com",
        page_size=50,
    )
    article_arr = arrange_news(news_article)
    return article_arr


def get_daily_news():

    daily_news = News.objects.filter(dtstr__contains=datetime.date.today().strftime("%Y-%m-%d"))
    print("daily news1", daily_news.count())
    if daily_news.count() == 0:
        print("no news")
        sources = "sunstar.com.ph,inquirer.net,gmanetwork.com,philstar.com,abs-cbn.com,mb.com.ph,manilatimes.net,cnnphilippines.com,tv5.com.ph,pna.gov.ph"

        daily_news = newscatcherapi.get_latest_headlines(
            lang="en,tl", sources=sources, page_size=12, countries="PH"
        )
        daily_news = arrange_news(daily_news, 1)
        save_news_to_database(daily_news)
    print("daily news", daily_news)
    return daily_news


def save_news_to_database(articles):
    for article in articles:
        news = News()
        news.title = article["title"]
        news.content = article["content"]
        news.excerpt = article["excerpt"]
        news.news_site_url = article["news_site_url"]
        news.author = article["author"]
        news.url = article["url"]
        news.media = article["media"]
        news.dtstr = article["dtstr"]
        news.save()


def phrase_conditions(message):
    message_arr = message.split(" ")
    if len(message_arr) <= 3 and len(message_arr) > 0:
        existing = News.objects.filter(
            Q(title__icontains=message)
            | Q(content__icontains=message)
            | Q(excerpt__icontains=message)
            )
        return existing
    elif len(message_arr) > 3:
        cache_news = News.objects.none()
        for i in message_arr:
            existing = News.objects.filter(
                Q(title__icontains=i)
                | Q(content__icontains=i)
                | Q(excerpt__icontains=i)
                )
            cache_news = cache_news.union(existing)
        return cache_news
    else:
        return []

def index(request):
    pred = ""
    news = ""
    message = ""
    daily_news = get_daily_news()
    try:
        if request.method == "POST":
            message = request.POST.get("message")
            existing = phrase_conditions(message)
            print(existing.count())
            if existing.count() != 0:
                news = existing
                print("CACHE HIT")
            else:
                news = get_news_api(message)
                print("CACHE MISS")
                if len(news) != 0:
                    save_news_to_database(news)
    except:
        pred = "Error"

    if news:
        news = replace_dtstr(news)

    context = {
        "predict": "Verified"
        if news
        else "Unverified"
        if not news and message
        else pred,
        "total_news": len(news),
        "month_old_news": len(
            list(
                filter(
                    lambda d: "month" in d["dtstr"] or "year" in d["dtstr"],
                    news,
                )
            )
        ),
        "news": news,
        "search_term": message,
        "daily_news": replace_dtstr(daily_news),
    }

    print(
        "NEWS=",
        len(news),
        "PRED=",
        context["predict"],
        "MONTH_OLD=",
        context["month_old_news"],
    )
    # print("CONTEXT=", context)
    return render(request, "news/index.html", context)


def replace_dtstr(news):
    return [
        {
            **(d.__dict__ if not isinstance(d, dict) else d),
            "dtstr": get_date_difference(
                d.get("dtstr") if isinstance(d, dict) else getattr(d, "dtstr")
            ),
        }
        for d in news
        if d
    ]
