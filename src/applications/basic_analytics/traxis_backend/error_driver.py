"""
The module for the driver to calculate metrics related to Traxis Backend error component.
"""

from pyspark.sql.functions import regexp_extract
from pyspark.sql.types import StructField, StructType, TimestampType, StringType

from common.basic_analytics.aggregations import Count
from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from util.kafka_pipeline_helper import start_basic_analytics_pipeline


class TraxisBackendError(BasicAnalyticsProcessor):
    """
    The processor implementation to calculate metrics related to Traxis Backend error component.
    """

    def _process_pipeline(self, read_stream):
        warn_events = read_stream.where("level == 'WARN'")
        error_events = read_stream.where("level == 'ERROR'")

        tva_ingest_error = warn_events \
            .where("message like '%One or more validation errors detected during tva ingest%'") \
            .aggregate(Count(group_fields=["hostname"],
                             aggregation_name=self._component_name + ".tva_ingest_error"))

        customer_provisioning_error = warn_events \
            .where("message like '%Unable to use alias%because alias is already used by%'") \
            .aggregate(Count(group_fields=["hostname"],
                             aggregation_name=self._component_name + ".customer_provisioning_error"))

        undefined_warnings = warn_events.where(
            "message not like '%Unable to use alias%because alias is already used by%' and "
            "message not like '%One or more validation errors detected during tva ingest%'"
        ).aggregate(Count(group_fields=["hostname"],
                          aggregation_name=self._component_name + ".undefined_warnings"))

        cassandra_errors = error_events \
            .where("message like '%Exception with cassandra node%'") \
            .withColumn("host", regexp_extract("message",
                                               r".*Exception\s+with\s+cassandra\s+node\s+\'([\d\.]+).*", 1)
                        ) \
            .aggregate(Count(group_fields=["hostname", "host"],
                             aggregation_name=self._component_name + ".cassandra_errors"))

        undefined_errors = error_events \
            .where("message not like '%Exception with cassandra node%'") \
            .aggregate(Count(group_fields=["hostname"],
                             aggregation_name=self._component_name + ".undefined_errors"))

        return [tva_ingest_error, customer_provisioning_error, undefined_warnings,
                cassandra_errors, undefined_errors]

    @staticmethod
    def create_schema():
        return StructType([
            StructField("@timestamp", TimestampType()),
            StructField("level", StringType()),
            StructField("message", StringType()),
            StructField("hostname", StringType())
        ])


def create_processor(configuration):
    """Method to create the instance of the processor"""
    return TraxisBackendError(configuration, TraxisBackendError.create_schema())


if __name__ == "__main__":
    start_basic_analytics_pipeline(create_processor)
