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
from datetime import datetime, timedelta

from nltk.corpus import stopwords
import nltk
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')



newscatcherapi = NewsCatcherApiClient(
    # Zaki API Key
    x_api_key="HZDdL8y0QYFdn_B9H1lpvof9doTdDloKLKSe8f2jAGY"
    # x_api_key="L2QU2I1Nm5xpHRIjAccgbfSMR_l6VUrxhiVI1Av8zMk"
    # this is for defense day (researcher's side)
    # x_api_key="3UVyIlDnQJ2uWr3bPh7XclVt-ba-jICgB8NnVUZ3Hp0"
    # this is for defense day (panel side)
    # x_api_key="1JuDVL2WGmKMlf6eClndPIj1h6dXIDkT0o6XYfMTZxY"
)

sources = "sunstar.com.ph,inquirer.net,gmanetwork.com,philstar.com,abs-cbn.com,mb.com.ph,manilatimes.net,cnnphilippines.com,tv5.com.ph,pna.gov.ph"

# def check_expired_data():
#     News.objects.filter(
#         posting_date__lte=datetime.now() - timedelta(minutes=1)
#     ).delete()
#     print("deleted")


def arrange_news(news_article):

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
            articles["media"] = data["media"]
            articles["dtstr"] = data["published_date"]
            article_arr.append(articles)
    print(article_arr)
    return article_arr


def get_news_api(message):
    q_message = message.replace(":", "")
    print("GET_NEWS_API=", message)

    news_article = newscatcherapi.get_search(
        q=q_message,
        lang="en,tl",
        countries="PH",
        sources=sources,
        page_size=50,
    )
    print("news_article", news_article["page_size"])
    if news_article["page_size"] != 0:
        search_news = arrange_news(news_article)
        save_news_to_database(search_news)
        existing = phrase_conditions(message)

    return existing

    # filtered_news = news_article.copy()
    # articles = []
    # msg = message.lower()

    # if "articles" in news_article:
    #     for d in filtered_news.pop("articles"):
    #         if (
    #             msg in d["title"].lower()
    #             or msg in d["excerpt"].lower()
    #             or msg in d["summary"].lower()
    #         ):
    #             articles.append(d)

    # filtered_news["articles"] = articles

    # print(
    #     f"""
    # OG={len(news_article["articles"])}
    # FILTERED={len(filtered_news["articles"])}
    # """
    # )

    # print("OGG=", news_article, "FILTERED=", filtered_news)

    # return arrange_news(filtered_news)


def get_daily_news():
    time_news = datetime.now() - timedelta(hours=8)
    daily_news = News.objects.filter(
        dtstr__contains=time_news.strftime("%Y-%m-%d") )
    print("daily news1", daily_news.count())
    if daily_news.count() == 0:
        print("no news")

        daily_news = newscatcherapi.get_latest_headlines(
            lang="en,tl", sources=sources, page_size=12, countries="PH"
        )
        daily_news = arrange_news(daily_news)
        save_news_to_database(daily_news, 1)
    print("daily news", daily_news)
    return daily_news


def save_news_to_database(articles, daily_news=0):
    for article in articles:
        news = News()
        news.title = article["title"]
        news.content = article["content"]
        news.excerpt = article["excerpt"]
        news.news_site_url = article["news_site_url"]
        news.author = article["author"]
        news.url = article["url"]
        if daily_news == 1:
            news.media = article["media"]
        news.dtstr = article["dtstr"]
        news.save()


def phrase_conditions(message):
    message_arr = message.split(" ")
    if len(message_arr) <= 3 and len(message_arr) > 0:
        print("message_arr", message_arr)
        existing = News.objects.filter(
            Q(title__icontains=message)
            | Q(content__icontains=message)
            | Q(excerpt__icontains=message)
        )
        print("existing", existing)
        return existing
    elif len(message_arr) > 3:
        q_message = message.replace(":", "")
        text_tokens = word_tokenize(q_message)
        tokens_without_sw = [word for word in text_tokens if not word in stopwords.words()]
        print(tokens_without_sw)
        cache_news = News.objects.none()
        for i in range (0, len(tokens_without_sw)):
            existing = News.objects.filter(
            Q(title__icontains=tokens_without_sw[i])
            & Q(title__icontains=tokens_without_sw[i-1])
            & Q(title__icontains=tokens_without_sw[i-2]))
            cache_news = cache_news.union(existing)
        print("cache_news", cache_news)
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
            print("message",message)
            existing = phrase_conditions(message)
            if existing.count() != 0:
                print("CACHE HIT")
                news = existing
            else:
                print("CACHE MISS")
                news = get_news_api(message)
                print("NEWS=", news)
    except Exception as e:
        print("ERROR=", e)
        pred = "Error"

    if news:
        news = replace_dtstr(news)

    context = {
        "predict": "Verified"
        if news
        else "Unverified"
        if not news and message
        else pred,
        "total_news": len(set([d["news_site_url"] for d in news])),
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
