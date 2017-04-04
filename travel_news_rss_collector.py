import feedparser
from bs4 import BeautifulSoup
import json
import time
import random

MAX_RANDOM_WAIT_TIME = 10

urls = {"CNN"    : "http://rss.cnn.com/rss/cnn_travel.rss", # Published
        "FOX"    : "http://feeds.foxnews.com/foxnews/internal/travel/mixed", # Published
        "abc"    : "http://feeds.abcnews.com/abcnews/travelheadlines",  # Published
        "reddit" : "https://www.reddit.com/r/travel.rss",  #updated
        "cnbc"   : "http://www.cnbc.com/id/10000739/device/rss/rss.html", # Published
        "nytimes": "http://rss.nytimes.com/services/xml/rss/nyt/Travel.xml" #Published
    }

etags = {"top_news": None, "health": None, "healthcare": None, "science": None}

while 1:
    for k, v in urls.items():
        d = feedparser.parse(v)
        for e in d.entries:
            if k == 'reddit':
                doc = json.dumps({"news_provider":k, "title":e.title.strip(), "summary":BeautifulSoup(e.summary).text.strip(), "id": e.id.strip(), "published": e.updated})
            else:
                doc = json.dumps({"news_provider": k, "title": e.title.strip(), "summary": BeautifulSoup(e.summary).text.strip(), "id": e.id.strip(), "published": e.published if e.has_key('published') else None})
            print "%s"%doc
    time.sleep(random.randint(1, MAX_RANDOM_WAIT_TIME))