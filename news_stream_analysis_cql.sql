-- KEYSPACE
CREATE KEYSPACE IF NOT EXISTS news_stream_analysis WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 2};
USE news_stream_analysis;

-- Results with the raw data
CREATE TABLE travel_news_data_results(
    id varchar PRIMARY KEY,
    news_provider varchar,
    published varchar,
    summary varchar,
    title varchar,
    topic_words varchar,
    results_date timestamp,
);

-- Example of the results
INSERT INTO travel_news_data_results("id", "news_provider", "published", "summary", "title", "topic_words", "results_date")
VALUES('http://abcnews.go.com/Lifestyle/video/walking-tour-land-pavilion-disneys-epcot-4508919000000',
 'abc',
 'Fri, 27 Jan 2017 15:26:40 -0500',
 'ABC News Genevieve Brown gives a tour of The Land Pavilion at Epcot Center with Les Frey.',
 'WATCH:  Walking Tour of The Land Pavilion at Disneys Epcot',
 'Genevieve, Disneys',
 '2011-02-03 04:05+0000'
 );

-- Raw Data
CREATE TABLE travel_news_data(
    id varchar PRIMARY KEY,
    news_provider varchar,
    published varchar,
    summary varchar,
    title varchar
);

INSERT INTO travel_news_data_results("id", "news_provider", "published", "summary", "title")
VALUES('http://abcnews.go.com/Lifestyle/video/walking-tour-land-pavilion-disneys-epcot-4508919000000',
 'abc',
 'Fri, 27 Jan 2017 15:26:40 -0500',
 'ABC News Genevieve Brown gives a tour of The Land Pavilion at Epcot Center with Les Frey.',
 'WATCH:  Walking Tour of The Land Pavilion at Disneys Epcot',
 );