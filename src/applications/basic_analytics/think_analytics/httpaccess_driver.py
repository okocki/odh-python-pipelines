"""
The module for the driver to calculate metrics related to Think Analytics HTTP access component.
"""
from pyspark.sql.types import StructField, StructType, TimestampType, StringType

from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from common.basic_analytics.aggregations import Count, Avg, DistinctCount
from util.kafka_pipeline_helper import start_basic_analytics_pipeline
from pyspark.sql.functions import col


class ThinkAnalyticsHttpAccessEventProcessor(BasicAnalyticsProcessor):
    """
    The processor implementation to calculate metrics related to Think Analytics HTTP access component.
    """

    def _process_pipeline(self, read_stream):

        http_access_stream = read_stream \
            .select("*",
                    col("contentSourceId").alias("content_source_id"),
                    col("clientType").alias("client_type"),
                    col("queryLanguage").alias("query_language"),
                    col("applyMarketingBias").alias("apply_marketing_bias"))

        response_code_stream = http_access_stream \
            .withColumn("response_code", col("response_code").cast("Int"))

        response_time_stream = http_access_stream \
            .withColumn("response_time", col("response_time").cast("Int"))

        return [self.__avg_response_time_by_method(response_time_stream),
                self.__avg_response_time(response_time_stream),
                self.__distinct_active_hosts(http_access_stream),
                self.__count_by_code(http_access_stream),
                self.__count_by_method(http_access_stream),
                self.__count_by_client_type(http_access_stream),
                self.__count_by_content_source_id_and_methods(http_access_stream),
                self.__count_by_marketing_bias_and_methods(http_access_stream),
                self.__count_responses(http_access_stream),
                self.__count_query_language(http_access_stream),
                self.__count_requests_by_hosts_and_status(response_code_stream),
                self.__count_requests_by_content_source_id_and_methods_and_status(response_code_stream),
                self.__count_requests_by_client_type_and_status(response_code_stream)]

    @staticmethod
    def create_schema():
        return StructType([
            StructField("@timestamp", TimestampType()),
            StructField("response_code", StringType()),
            StructField("response_time", StringType()),
            StructField("contentSourceId", StringType()),
            StructField("clientType", StringType()),
            StructField("method", StringType()),
            StructField("queryLanguage", StringType()),
            StructField("applyMarketingBias", StringType()),
            StructField("hostname", StringType())
        ])

    def __avg_response_time_by_method(self, read_stream):
        return read_stream \
            .where("method is not null") \
            .aggregate(Avg(group_fields=["hostname", "method"],
                           aggregation_field="response_time",
                           aggregation_name=self._component_name))

    def __avg_response_time(self, read_stream):
        return read_stream \
            .aggregate(Avg(group_fields=["hostname"],
                           aggregation_field="response_time",
                           aggregation_name=self._component_name))

    def __distinct_active_hosts(self, read_stream):
        return read_stream \
            .aggregate(DistinctCount(aggregation_field="hostname",
                                     aggregation_name=self._component_name))

    def __count_by_code(self, read_stream):
        return read_stream \
            .where("response_code is not null") \
            .aggregate(Count(group_fields=["hostname", "response_code"],
                             aggregation_name=self._component_name))

    def __count_by_method(self, read_stream):
        return read_stream \
            .where("method is not null") \
            .aggregate(Count(group_fields=["hostname", "method"],
                             aggregation_name=self._component_name))

    def __count_by_client_type(self, read_stream):
        return read_stream \
            .where("client_type is not null") \
            .aggregate(Count(group_fields=["client_type"],
                             aggregation_name=self._component_name))

    def __count_by_content_source_id_and_methods(self, read_stream):
        return read_stream \
            .where("method is not null") \
            .aggregate(Count(group_fields=["content_source_id", "method"],
                             aggregation_name=self._component_name))

    def __count_by_marketing_bias_and_methods(self, read_stream):
        return read_stream \
            .where("method is not null") \
            .aggregate(Count(group_fields=["apply_marketing_bias", "method"],
                             aggregation_name=self._component_name))

    def __count_responses(self, read_stream):
        return read_stream \
            .aggregate(Count(group_fields=["hostname"],
                             aggregation_name=self._component_name + ".responses"))

    def __count_query_language(self, read_stream):
        return read_stream \
            .where("query_language is not null") \
            .where("method == 'lgiAdaptiveSearch'") \
            .aggregate(Count(group_fields=["query_language"],
                             aggregation_name=self._component_name))

    def __count_requests_by_hosts_and_status(self, read_stream):
        return read_stream \
            .where("hostname is not null") \
            .withColumn("response_successful", col("response_code").between(200, 299).cast("string")) \
            .aggregate(Count(group_fields=["hostname", "response_successful"],
                             aggregation_name=self._component_name))

    def __count_requests_by_content_source_id_and_methods_and_status(self, read_stream):
        return read_stream \
            .where("method is not null") \
            .withColumn("response_successful", col("response_code").between(200, 299).cast("string")) \
            .aggregate(Count(group_fields=["content_source_id", "method", "response_successful"],
                             aggregation_name=self._component_name))

    def __count_requests_by_client_type_and_status(self, read_stream):
        return read_stream \
            .where("client_type is not null") \
            .withColumn("response_successful", col("response_code").between(200, 299).cast("string")) \
            .aggregate(Count(group_fields=["client_type", "response_successful"],
                             aggregation_name=self._component_name))


def create_processor(configuration):
    """Method to create the instance of the processor"""
    return ThinkAnalyticsHttpAccessEventProcessor(configuration, ThinkAnalyticsHttpAccessEventProcessor.create_schema())


if __name__ == "__main__":
    start_basic_analytics_pipeline(create_processor)
