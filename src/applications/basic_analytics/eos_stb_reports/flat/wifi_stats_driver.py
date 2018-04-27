"""
Module for counting all general analytics metrics for EOS STB Wifi Report
"""
from pyspark.sql.types import StructField, StructType, TimestampType, StringType, ArrayType, IntegerType, LongType

from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from util.kafka_pipeline_helper import start_basic_analytics_pipeline
from common.basic_analytics.aggregations import DistinctCount, Avg
from pyspark.sql.functions import col, from_unixtime


class WifiReportEventProcessor(BasicAnalyticsProcessor):
    """
    Class that's responsible to process pipelines for Wifi Reports
    """

    def _prepare_timefield(self, data_stream):
        return data_stream .withColumn("@timestamp", from_unixtime(col("WiFiStats.ts") / 1000).cast(TimestampType()))

    def _process_pipeline(self, read_stream):

        self._common_wifi_pipeline = read_stream \
            .select("@timestamp",
                    "WiFiStats.*",
                    col("header.viewerID").alias("viewer_id"))

        return [self.distinct_total_wifi_network_types_count(),
                self.wireless_average_upstream_kbps(),
                self.wireless_average_downstream_kbps(),
                self.count_distinct_active_stb_wifi()]

    @staticmethod
    def create_schema():
        return StructType([
            StructField("header", StructType([
                StructField("viewerID", StringType())
            ])),
            StructField("WiFiStats", StructType([
                StructField("ts", LongType()),
                StructField("type", StringType()),
                StructField("rxKbps", IntegerType()),
                StructField("txKbps", IntegerType()),
                StructField("RSSi", ArrayType(IntegerType()))
            ]))
        ])

    def distinct_total_wifi_network_types_count(self):
        return self._common_wifi_pipeline \
            .where((col("rxKbps") >= 1) | (col("txKbps") >= 1)) \
            .aggregate(DistinctCount(aggregation_field="viewer_id",
                                     aggregation_name=self._component_name + ".wifi_network_total"))

    def wireless_average_upstream_kbps(self):
        return self._common_wifi_pipeline \
            .where("txKbps is not NULL") \
            .aggregate(Avg(aggregation_field="txKbps",
                           aggregation_name=self._component_name + ".wireless.average_upstream_kbps"))

    def wireless_average_downstream_kbps(self):
        return self._common_wifi_pipeline \
            .where("rxKbps is not NULL") \
            .aggregate(Avg(aggregation_field="rxKbps",
                           aggregation_name=self._component_name + ".wireless.average_downstream_kbps"))

    def count_distinct_active_stb_wifi(self):
        return self._common_wifi_pipeline \
            .where("rxKbps > 0") \
            .aggregate(DistinctCount(aggregation_field="viewer_id",
                                     aggregation_name=self._component_name + ".active_stb_wifi"))


def create_processor(configuration):
    """
    Method to create the instance of the processor
    """
    return WifiReportEventProcessor(configuration, WifiReportEventProcessor.create_schema())


if __name__ == "__main__":
    start_basic_analytics_pipeline(create_processor)
