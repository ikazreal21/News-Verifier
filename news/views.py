from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import *
from .forms import *

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split

from newscatcherapi import NewsCatcherApiClient

newscatcherapi = NewsCatcherApiClient(x_api_key='g8EYZLLr3R6q7sBhuK6LWPDlPVV3T86WsZAo0v2NYt8')

tfvect = TfidfVectorizer(stop_words='english', max_df=0.7)
loaded_model = pickle.load(open('news\model.pkl', 'rb'))
dataframe = pd.read_csv('news\\news.csv')
x = dataframe['text']
y = dataframe['label']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

def fake_news_det(news):
    tfid_x_train = tfvect.fit_transform(x_train)
    tfid_x_test = tfvect.transform(x_test)
    input_data = [news]
    vectorized_input_data = tfvect.transform(input_data)
    prediction = loaded_model.predict(vectorized_input_data)
    return prediction


def get_news_api(message):

    query = f'{message}'
    news_article = newscatcherapi.get_search(
        q=query,
        lang='en',
        countries='PH',
        sources='cnnphilippines.com,philstar.com,manilatimes.net,mb.com.ph,\
        tv5.com.ph,inquirer.net,dzrh.com.ph,abs-cbn.com,gmanetwork.com',
        page_size=50
        )
    
    article_arr = []
    if news_article['page_size'] != 0:
        for data in news_article['articles']:
            articles = {}
            articles["title"] = data["title"]
            articles["author"] = data["author"]
            articles["excerpt"] = data["excerpt"]
            articles["summary"] = data["summary"]
            articles["clean_url"] = data["clean_url"]
            article_arr.append(articles)

    return article_arr


def save_news_to_database(phrase, articles):
    for article in articles:
        news = News()
        news.phrase = phrase
        news.title = article["title"]
        news.content = article["summary"]
        news.excerpt = article["excerpt"]
        news.url = article["clean_url"]
        news.author = article["author"]
        news.save()

def index(request):
    pred = ''
    news = ''
    phraseform = SavePhrase()
    if request.method == 'POST':
        message = request.POST.get('message')
        existing = News.objects.filter(phrase=message)
        if existing.count() != 0:
            news = existing
        else:
            phraseform = SavePhrase(request.POST)
            if phraseform.is_valid():
                phraseform.save()
                message = phraseform.cleaned_data.get("message")
                news = get_news_api(message)
                if len(news) != 0:
                    save_news_to_database(message, news)
                else: 
                    pred = fake_news_det(message)
                    pred = 'Unverified'
                print(pred)
                print(news)
                input("Enter")
    context = {'predict': pred, 'news': news}
    return render(request, 'news/index.html', context)