This application categorize the streamed news using the LDA(Latent Dirichlet allocation) algorithm using the PySpark. 

Use of Apache Flume:
    The Apache Flume runs travel_news_rss_collector.py as a source using the python command.
    The python application file captures the RSS feed from the different travel news sources.
    It uses the avro sink to pass the data to the Spark Application using the Memchannel

Use of Apache Spark:
    The Apache Spark is used to analyze the news stream into the mini batch processing. The topics of the news stream is identified using the LDA algorithm  and the news stories are chosen based on those topics identified by the LDA analysis. 
    
Use of Apache Cassandra:
    The spark application saves both the raw data and the clusterd results into the Cassandra database. The data can be easily stored as the columner data. 

The schema for the results data as below.

id|news_provider|published|results_date|summary|title|topic_word

The result schema is stored with the raw data for the further processing.
