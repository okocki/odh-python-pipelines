"""
Module for counting all general analytics metrics for EOS STB ApplicationsReport Report
"""
from pyspark.sql.types import StructField, StructType, TimestampType, StringType, LongType

from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from common.spark_utils.custom_functions import convert_epoch_to_iso
from util.kafka_pipeline_helper import start_basic_analytics_pipeline
from common.basic_analytics.aggregations import DistinctCount, Count
from pyspark.sql.functions import col


class ApplicationsReportEventProcessor(BasicAnalyticsProcessor):
    """
    Class that's responsible to process pipelines for ApplicationsReport Reports
    """
    def _prepare_timefield(self, read_stream):
        return convert_epoch_to_iso(read_stream, "ApplicationsReport.ts", "@timestamp")

    def _process_pipeline(self, read_stream):

        applications_report_stream = read_stream \
            .select("@timestamp", "ApplicationsReport.*", col("header.viewerID").alias("viewer_id"))

        return [self.__distinct_active_stb(applications_report_stream),
                self.__distinct_active_stb_netflix(applications_report_stream),
                self.__distinct_active_stb_youtube(applications_report_stream),
                self.__distinct_active_stb_app_started(applications_report_stream),
                self.__total_app_events(applications_report_stream)]

    @staticmethod
    def create_schema():
        return StructType([
            StructField("@timestamp", TimestampType()),
            StructField("header", StructType([
                StructField("viewerID", StringType())
            ])),
            StructField("ApplicationsReport", StructType([
                StructField("ts", LongType()),
                StructField("provider_id", StringType()),
                StructField("event_type", StringType())
            ]))
        ])

    def __distinct_active_stb(self, applications_report_stream):
        return applications_report_stream \
            .aggregate(DistinctCount(group_fields=["provider_id", "event_type"], aggregation_field="viewer_id",
                                     aggregation_name=self._component_name,
                                     aggregation_window=self._get_interval_duration("uniqCountWindow")))

    def __distinct_active_stb_netflix(self, read_stream):
        return read_stream \
            .where("provider_id = 'netflix'") \
            .aggregate(DistinctCount(aggregation_field="viewer_id",
                                     aggregation_name=self._component_name + ".netflix"))

    def __distinct_active_stb_youtube(self, read_stream):
        return read_stream \
            .where("provider_id = 'youtube'") \
            .aggregate(DistinctCount(aggregation_field="viewer_id",
                                     aggregation_name=self._component_name + ".youtube"))

    def __distinct_active_stb_app_started(self, read_stream):
        return read_stream \
            .where("event_type = 'app_started'") \
            .aggregate(DistinctCount(group_fields=["provider_id"],
                                     aggregation_field="viewer_id",
                                     aggregation_name=self._component_name + ".app_started"))

    def __total_app_events(self, applications_report_stream):
        return applications_report_stream \
            .aggregate(Count(group_fields=["provider_id", "event_type"], aggregation_field="viewer_id",
                                     aggregation_name=self._component_name))

def create_processor(configuration):
    """
    Method to create the instance of the processor
    """
    return ApplicationsReportEventProcessor(configuration, ApplicationsReportEventProcessor.create_schema())


if __name__ == "__main__":
    start_basic_analytics_pipeline(create_processor)
