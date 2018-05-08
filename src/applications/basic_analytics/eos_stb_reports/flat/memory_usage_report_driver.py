"""
Basic analytics driver for STB Memory usage report.
"""
from pyspark.sql.types import StructType, StructField, TimestampType, StringType, LongType

from common.basic_analytics.aggregations import Avg
from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from common.spark_utils.custom_functions import convert_epoch_to_iso
from util.kafka_pipeline_helper import start_basic_analytics_pipeline


class MemoryUsageReportEventProcessor(BasicAnalyticsProcessor):
    """
    Basic analytics driver for STB Memory usage report.
    """

    def _prepare_timefield(self, read_stream):
        return convert_epoch_to_iso(read_stream, "MemoryUsage.ts", "@timestamp")

    def _process_pipeline(self, read_stream):

        memory_usage_report_stream = read_stream \
            .select("@timestamp", "MemoryUsage.*")

        return [self.avg_memory_used_kb(memory_usage_report_stream),
                self.avg_memory_cached_kb(memory_usage_report_stream),
                self.avg_memory_free_kb(memory_usage_report_stream)]

    @staticmethod
    def create_schema():
        return StructType([
            StructField("@timestamp", TimestampType()),
            StructField("MemoryUsage", StructType([
                StructField("ts", LongType()),
                StructField("usedKb", StringType()),
                StructField("cachedKb", StringType()),
                StructField("freeKb", StringType())
            ]))
        ])

    def avg_memory_used_kb(self, read_stream):
        return read_stream \
            .where("usedKb is not NULL") \
            .aggregate(Avg(aggregation_field="usedKb",
                           aggregation_name=self._component_name))

    def avg_memory_cached_kb(self, read_stream):
        return read_stream \
            .where("cachedKb is not NULL") \
            .aggregate(Avg(aggregation_field="cachedKb",
                           aggregation_name=self._component_name))

    def avg_memory_free_kb(self, read_stream):
        return read_stream \
            .where("freeKb is not NULL") \
            .aggregate(Avg(aggregation_field="freeKb",
                           aggregation_name=self._component_name))


def create_processor(configuration):
    """Method to create the instance of the processor"""
    return MemoryUsageReportEventProcessor(configuration, MemoryUsageReportEventProcessor.create_schema())


if __name__ == '__main__':
    start_basic_analytics_pipeline(create_processor)
