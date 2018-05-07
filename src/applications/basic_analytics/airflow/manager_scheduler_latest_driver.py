"""
The module for the driver to calculate metrics related to Airflow Manager scheduler component.
"""
from pyspark.sql.types import StructField, StructType, TimestampType, StringType

from common.basic_analytics.basic_analytics_processor import BasicAnalyticsProcessor
from common.basic_analytics.aggregations import Count
from util.kafka_pipeline_helper import start_basic_analytics_pipeline


class AirflowManagerScheduler(BasicAnalyticsProcessor):
    """
    The processor implementation to calculate metrics related to Airflow Manager scheduler component.
    """

    def _process_pipeline(self, read_stream):
        self._common_pipeline = read_stream \
            .select("@timestamp",
                    "action",
                    "status",
                    "dag")
        return [self.processed_dags_count(),
                self.dag_total_initiated_executions()]

    @staticmethod
    def create_schema():
        return StructType([
            StructField("@timestamp", TimestampType()),
            StructField("script", StringType()),
            StructField("level", StringType()),
            StructField("message", StringType()),
            StructField("hostname", StringType()),
            StructField("status", StringType()),
            StructField("action", StringType()),
            StructField("dag", StringType())
        ])

    def processed_dags_count(self):
        return self._common_pipeline \
            .filter("action = 'RUN'") \
            .aggregate(Count(group_fields=["status"],
                             aggregation_name=self._component_name))

    def dag_total_initiated_executions(self):
        return self._common_pipeline \
            .filter("action = 'CREATE'") \
            .aggregate(Count(aggregation_name=self._component_name + ".initiated_executions"))


def create_processor(configuration):
    """Method to create the instance of the Airflow Manager Scheduler processor"""

    return AirflowManagerScheduler(configuration, AirflowManagerScheduler.create_schema())


if __name__ == "__main__":
    start_basic_analytics_pipeline(create_processor)
