"""
Basic analytics driver for STB Display Report.
"""
from pyspark.sql.functions import from_unixtime, col
from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from util.kafka_pipeline_helper import start_basic_analytics_pipeline
from pyspark.sql.types import StructField, StructType, TimestampType, StringType
from common.basic_analytics.aggregations import Count


class DisplayStbBasicAnalytics(BasicAnalyticsProcessor):
    """
    Basic analytics driver for STB Display Report.
    """

    def _process_pipeline(self, stream):
        aggregation_fields = ["SettingsReport_cpe_aspectRatio", "SettingsReport_cpe_hdmiResolution"]
        dimensions = ["hardwareVersion", "firmwareVersion", "appVersion", "asVersion"]

        aggregations = [Count(group_fields=self.immutable_append_and_return(dimensions, field),
                              aggregation_name=self._component_name) for field in aggregation_fields]

        return stream.aggregate(aggregations)

    def _prepare_timefield(self, data_stream):
        return data_stream.withColumn("@timestamp", from_unixtime(col("timestamp") / 1000).cast(TimestampType()))

    @staticmethod
    def immutable_append_and_return(lst, item):
        copy = list(lst)
        copy.append(item)
        return copy

    @staticmethod
    def create_schema():
        return StructType([
            StructField("timestamp", StringType()),
            StructField("hardwareVersion", StringType()),
            StructField("firmwareVersion", StringType()),
            StructField("appVersion", StringType()),
            StructField("asVersion", StringType()),
            StructField("SettingsReport_cpe_aspectRatio", StringType()),
            StructField("SettingsReport_cpe_hdmiResolution", StringType()),
        ])


def create_processor(configuration):
    """Method to create the instance of the processor"""
    return DisplayStbBasicAnalytics(configuration, DisplayStbBasicAnalytics.create_schema())


if __name__ == "__main__":
    start_basic_analytics_pipeline(create_processor)
