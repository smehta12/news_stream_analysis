# TODO: Update to LSH/MinHash for finding trending news whenever pyspark API available. http://spark.apache.org/docs/latest/ml-features.html#locality-sensitive-hashing
# TODO: Create a seperate module for the data scrubbing. So it can be used for both streaming and the Oozie job data.

from __future__ import print_function
import json
import datetime

from pyspark import SparkContext

from pyspark.streaming import StreamingContext
from pyspark.streaming.flume import FlumeUtils

from pyspark.sql import SparkSession
from pyspark.sql import functions as fn

from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import CountVectorizer, Tokenizer
from pyspark.ml.clustering import LDA


def getSparkSessionInstance(sparkConf):
    if ('sparkSessionSingletonInstance' not in globals()):
        sess = SparkSession \
            .builder \
            .config(conf=sparkConf) \
            .getOrCreate()
        globals()['sparkSessionSingletonInstance'] = sess
    return globals()['sparkSessionSingletonInstance']


def get_trending_news(rdd):
    if not rdd.isEmpty():
        spark = getSparkSessionInstance(rdd.context.getConf())

        df = spark.createDataFrame(rdd)

        # Append the title and summary together
        df_news_concat = df.withColumn("news_content", fn.concat_ws(" ", df.title, df.summary))

        df_punc_removed = df_news_concat.withColumn("news_content_removed",
                                                    fn.regexp_replace(df_news_concat.news_content, "\p{Punct}", ""))

        udf_remove_unicode = fn.udf(lambda x: x.encode("ascii", "ignore").decode("ascii"))
        df_news_content_ascii = df_punc_removed.withColumn("news_content_ascii",
                                                           udf_remove_unicode(df_punc_removed.news_content_removed))

        # insert raw data to the cassandra table
        df_news_content_ascii.select("id", "news_provider", "published", "summary", "title") \
            .write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table="travel_news_data", keyspace="news_stream_analysis") \
            .save(mode="append")

        tokenizer = Tokenizer(inputCol="news_content_ascii", outputCol="content_words")
        df_tokenized_content = tokenizer.transform(df_news_content_ascii).drop("news_content")

        remover = StopWordsRemover(inputCol="content_words", outputCol="filtered_words")
        stop_words = remover.loadDefaultStopWords("english")
        stop_words.extend(
            ['', "travel", "trip", "submitted", "abc", "reditt", "by", "time", "timing", "comments", "comment", "thank",
             "link",
             "im", "thanks", "would", "like", "get", "good", "go", "may", "also", "going", "dont", "want", "see",
             "take", "looking", ""])
        remover.setStopWords(stop_words)
        df_stop_words_removed = remover.transform(df_tokenized_content).drop("content_words")

        cv = CountVectorizer(inputCol="filtered_words", outputCol="rawFeatures")
        cv_model = cv.fit(df_stop_words_removed)
        df_tf_data = cv_model.transform(df_stop_words_removed)
        df_features = df_tf_data.select(df_tf_data.rawFeatures.alias("features"))

        def convert_term_indices_to_term(term_indices, vocab):
            terms = []
            for t in term_indices:
                terms.append(vocab[t])

            return str(terms)

        # LDA
        lda = LDA(k=5, maxIter=50, learningOffset=8192.0, learningDecay=0.50)
        model = lda.fit(df_features)
        df_topics = model.describeTopics()

        fn_term_indices_to_term = fn.udf(convert_term_indices_to_term)
        vocab_lit = fn.array(*[fn.lit(k) for k in cv_model.vocabulary])
        df_lda_result = df_topics.withColumn("terms", fn_term_indices_to_term("termIndices", vocab_lit))
        df_lda_result.select("topic", "termIndices", "terms").show(truncate=False)

        df_lda_result.cache()

        lda_terms = df_lda_result.select("terms").collect()
        lda_terms_list = [str(i.terms) for i in lda_terms]

        # based on model terms choose news stories
        for term_list in lda_terms_list:
            s = []
            topic_words = term_list[1:-1].split(",")
            for term in topic_words:
                term = term.split("'")[1]
                s.append(r"(^|\W)" + str(term) + r"($|\W)")
            rx = '|'.join('(?:{0})'.format(x.strip()) for x in s)
            df_results = df_news_content_ascii.filter(df_news_content_ascii['news_content_ascii'].rlike(rx))
            df_results = df_results.withColumn("topic_words", fn.lit(str(topic_words)[1:-1]))
            df_results = df_results.withColumn("results_date", fn.lit(datetime.datetime.now()))

            # insert results with the raw data to the cassandra table
            df_results.select("id", "news_provider", "published", "summary", "title", "topic_words", "results_date") \
                .write \
                .format("org.apache.spark.sql.cassandra") \
                .mode("append") \
                .options(table="travel_news_data_results", keyspace="news_stream_analysis") \
                .save(mode="append")


def main():
    sc = SparkContext(appName="News_Steam_Analysis")

    # Create the flume stream
    ssc = StreamingContext(sc, 300)  # Use the time here to decide what should be the interval for the top stories.
    flume_strm = FlumeUtils.createStream(ssc, "localhost", 9999, bodyDecoder=lambda x: x)

    lines = flume_strm.map(lambda (k, v): json.loads(v))

    lines.foreachRDD(get_trending_news)

    ssc.start()
    ssc.awaitTermination()


if __name__ == '__main__':
    main()
