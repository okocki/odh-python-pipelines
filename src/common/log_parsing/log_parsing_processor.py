"""Module for common LogParsingProcessor"""
from common.log_parsing.metadata import ParsingException

from pyspark.sql.types import *
from pyspark.sql.functions import *

import json
from datetime import date, datetime
import pytz


class LogParsingProcessor(object):
    """
    Pipeline for log parsing
    """

    def __init__(self, configuration, event_creators_tree):
        self.__event_creators_tree = event_creators_tree
        self.__dlq_topic = configuration.property("kafka.topics.dlq")

    def create(self, read_stream):
        create_full_event_udf = udf(self.__create_full_event, self.__get_udf_result_schema())
        return [self._extract_json(read_stream)
                    .select(create_full_event_udf("json").alias("result"))
                    .selectExpr("result.topic AS topic", "result.json AS value")]

    def _extract_json(self, stream):
        return stream \
            .select(from_json(stream["value"].cast("string"), self.__get_message_schema()).alias("json"))

    @staticmethod
    def __get_message_schema():
        return StructType([
            StructField("beat", StructType([
                StructField("hostname", StringType())
            ])),
            StructField("topic", StringType()),
            StructField("source", StringType()),
            StructField("message", StringType())
        ])

    @staticmethod
    def __get_udf_result_schema():
        return StructType([
            StructField("topic", StringType()),
            StructField("json", StringType())
        ])

    def __create_full_event(self, row):
        try:
            source_configuration = self.__event_creators_tree.get_parsing_context(row)
            result = source_configuration.event_creator.create(row)
            topic = source_configuration.output_topic
        except ParsingException as exception:
            topic = self.__dlq_topic
            result = {"message": row.message, "reason": exception.message}

        return topic, json.dumps(self._enrich_result(result, row), default=self.__json_serial)

    @staticmethod
    def _enrich_result(result, row):
        result.update({"hostname": row.beat.hostname, "environment": row.topic, "source": row.source})
        return result

    def __get_parsing_objects(self, row):
        return self.__event_creators_tree.get_parsing_objects(row)

    @staticmethod
    def __json_serial(value):
        """
        Transform date to UTC zone and convert to string in iso format
        :param value: all fields for filling json
        :return: string in format YYYY.DD.MMTHH:MM:SS[.SSS]Z
        """
        if isinstance(value, (datetime, date)):
            timestamp_with_timezone = value.astimezone(pytz.utc)
            iso_timestamp = timestamp_with_timezone.strftime("%Y-%m-%dT%H:%M:%S.%f")
            if len(iso_timestamp) == 26:
                return iso_timestamp[:23] + "Z"
            else:
                return iso_timestamp + ".000Z"
        raise TypeError("Type %s not serializable" % type(value))
