from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import get_date_difference

from .models import *
from .forms import *

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split

from newscatcherapi import NewsCatcherApiClient
from django.db.models import Q
import datetime

newscatcherapi = NewsCatcherApiClient(
    x_api_key="g8EYZLLr3R6q7sBhuK6LWPDlPVV3T86WsZAo0v2NYt8"
)

tfvect = TfidfVectorizer(stop_words="english", max_df=0.7)

# linux
loaded_model = pickle.load(open("news/model.pkl", "rb"))
dataframe = pd.read_csv("news/news.csv")
# windows
# loaded_model = pickle.load(open("news\model.pkl", "rb"))
# dataframe = pd.read_csv('news\\news.csv')
x = dataframe["text"]
y = dataframe["label"]
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=0
)


def fake_news_det(news):
    tfid_x_train = tfvect.fit_transform(x_train)
    tfid_x_test = tfvect.transform(x_test)
    input_data = [news]
    vectorized_input_data = tfvect.transform(input_data)
    prediction = loaded_model.predict(vectorized_input_data)
    return prediction


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
            else:
                pred = fake_news_det(message)
                if pred[0] == "FAKE":
                    pred = "Unverified"
                elif pred[0] == "REAL":
                    pred = "Verified"
                else:
                    pred = "Error"

            print("PREDICTION=", pred)
    print("NEWS=", news)
    context = {
        "predict": pred,
        "news": [
            {**d.__dict__, "dtstr": get_date_difference(getattr(d, "dtstr"))}
            for d in news
        ],
        "search_term": message,
    }
    return render(request, "news/index.html", context)
