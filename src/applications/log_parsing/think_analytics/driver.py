"""Spark driver for parsing message from Think Analytics component"""
import sys

from common.log_parsing.dict_event_creator.event_with_url_creator import EventWithUrlCreator
from common.kafka_pipeline import KafkaPipeline
from common.log_parsing.composite_event_creator import CompositeEventCreator
from common.log_parsing.dict_event_creator.event_creator import EventCreator as DictEventCreator
from common.log_parsing.dict_event_creator.parsers.regexp_matches_parser import RegexpMatchesParser
from common.log_parsing.event_creator_tree.multisource_configuration import SourceConfiguration, MatchField
from common.log_parsing.list_event_creator.event_creator import EventCreator
from common.log_parsing.dict_event_creator.mutate_event_creator import MutateEventCreator, FieldsMapping
from common.log_parsing.list_event_creator.parsers.csv_parser import CsvParser
from common.log_parsing.list_event_creator.parsers.regexp_parser import RegexpParser
from common.log_parsing.list_event_creator.parsers.splitter_parser import SplitterParser
from common.log_parsing.log_parsing_processor import LogParsingProcessor
from common.log_parsing.metadata import Metadata, StringField, ParsingException
from common.log_parsing.timezone_metadata import ConfigurableTimestampField
from util.utils import Utils


def create_event_creators(configuration):
    """
    Tree of different parsers for all types of logs for THINK ANALYTICS
    :param configuration: YML config
    :return: Tree of event_creators
    """
    timezone_name = configuration.property("timezone.name")
    timezones_priority = configuration.property("timezone.priority", "idc")

    duration_event_creator = MutateEventCreator(None,
                                                [FieldsMapping(["started_script", "finished_script", "finished_time",
                                                                "@timestamp"], "duration", duration_update)])

    concat_httpaccess_timestamp_event_creator = MutateEventCreator(
        Metadata(
            [ConfigurableTimestampField("timestamp", "%d/%b/%Y:%H:%M:%S",
                                        timezone_name, timezones_priority, "@timestamp",
                                        include_timezone=True)]),
        [FieldsMapping(["date", "time"], "timestamp", agg_func=lambda x, y: (x + " " + y)[1:-1],
                       remove_intermediate_fields=True)])

    concat_central_timestamp_event_creator = MutateEventCreator(
        Metadata(
            [ConfigurableTimestampField("timestamp", "%a %d/%m/%y %H:%M:%S",
                                        timezone_name, timezones_priority, "@timestamp")]),
        [FieldsMapping(["date", "time"], "timestamp", remove_intermediate_fields=True)])

    traxis_profile_id_event_creator = MutateEventCreator(
        fields_mappings=[FieldsMapping(["subscriberId"], "traxis-profile-id", lambda x: x, True)])

    content_item_id_event_creator = MutateEventCreator(fields_mappings=[
        FieldsMapping(["contentItemId"], "crid", lambda x: "crid{}".format(x.split('crid')[-1]), False)])

    int_request_id_event_creator = MutateEventCreator(
        fields_mappings=[FieldsMapping(["intRequestId"], "request-id", lambda x: x, True)])

    return MatchField("source", {
        "localhost_access_log": SourceConfiguration(
            CompositeEventCreator()
            .add_source_parser(
                EventCreator(
                    Metadata([
                        StringField("date"),
                        StringField("time"),
                        StringField("ip"),
                        StringField("thread"),
                        StringField("http_method"),
                        StringField("url"),
                        StringField("http_version"),
                        StringField("response_code"),
                        StringField("response_time")
                    ]),
                    SplitterParser(delimiter=" ", is_trim=True)
                )
            )
            .add_intermediate_result_parser(concat_httpaccess_timestamp_event_creator)
            .add_intermediate_result_parser(EventWithUrlCreator(delete_source_field=True, keys_to_underscore=False))
            .add_intermediate_result_parser(traxis_profile_id_event_creator)
            .add_intermediate_result_parser(content_item_id_event_creator)
            .add_intermediate_result_parser(int_request_id_event_creator),
            Utils.get_output_topic(configuration, "httpaccess")
        ),
        "RE_SystemOut.log": SourceConfiguration(
            EventCreator(
                Metadata([
                    ConfigurableTimestampField("@timestamp", "%d/%m/%y %H:%M:%S.%f", timezone_name, timezones_priority,
                                               dayfirst=True, use_smart_parsing=True),
                    StringField("level"),
                    StringField("script"),
                    StringField("message")
                ]),
                RegexpParser(
                    r"^\[(?P<timestamp>\d{2}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\s\D+?)\] "
                    r"(?P<level>\w+?)\s+?-\s+?(?P<script>\S+?)\s+?:\s+?(?P<message>.*)")
            ),
            Utils.get_output_topic(configuration, "resystemout")
        ),
        "REMON_SystemOut.log": SourceConfiguration(
            EventCreator(
                Metadata([
                    ConfigurableTimestampField("@timestamp", None, timezone_name, timezones_priority,
                                               dayfirst=True, use_smart_parsing=True),
                    StringField("level"),
                    StringField("script"),
                    StringField("type"),
                    StringField("message")
                ]),
                RegexpParser(
                    r"^\[(?P<timestamp>\d{2}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}.\d{3}\s\D+?)\] "
                    r"(?P<level>\w+?)\s+?-\s+?(?P<script>\S+?)\s+?:\s+?\[(?P<type>\S+?)\]\s+?-\s+?(?P<message>.*)")
            ),
            Utils.get_output_topic(configuration, "remonsystemout")
        ),
        "Central.log": SourceConfiguration(
            CompositeEventCreator()
                .add_source_parser(
                EventCreator(
                    Metadata([
                        StringField("date"),
                        StringField("time"),
                        StringField("level"),
                        StringField("message"),
                        StringField("thread"),
                        StringField("c0"),
                        StringField("c1"),
                        StringField("c2"),
                        StringField("role")
                    ]),
                    CsvParser(",", '"')
                )
            )
                .add_intermediate_result_parser(concat_central_timestamp_event_creator),
            Utils.get_output_topic(configuration, "central")
        ),
        "thinkenterprise.log": SourceConfiguration(
            EventCreator(
                Metadata([
                    ConfigurableTimestampField("@timestamp", "%Y-%m-%d %H:%M:%S,%f", timezone_name, timezones_priority),
                    StringField("level"),
                    StringField("message")
                ]),
                RegexpParser(
                    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"
                    r":\s+?(?P<level>\w+?)\s+?-\s+?(?P<message>.*)")
            ),
            Utils.get_output_topic(configuration, "thinkenterprise")
        ),
        "gcollector.log": SourceConfiguration(
            EventCreator(
                Metadata([
                    ConfigurableTimestampField("@timestamp", "%Y-%m-%dT%H:%M:%S.%f", timezone_name, timezones_priority,
                                               include_timezone=True),
                    StringField("process_uptime"),
                    StringField("message")
                ]),
                RegexpParser(
                    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}.\d{4})"
                    r":\s+?(?P<process_uptime>\d+?\.\d{3}):\s+?(?P<message>.*)")
            ),
            Utils.get_output_topic(configuration, "gcollector")
        ),
        "server.log": SourceConfiguration(
            EventCreator(
                Metadata([
                    ConfigurableTimestampField("@timestamp", "%Y-%m-%d %H:%M:%S,%f", timezone_name, timezones_priority),
                    StringField("level"),
                    StringField("class_name"),
                    StringField("thread"),
                    StringField("message")
                ]),
                RegexpParser(
                    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+?"
                    r"(?P<level>\w+?)\s+?\[(?P<class_name>.+?)\]\s+?\((?P<thread>.+?)\)\s+?(?P<message>.*)")
            ),
            Utils.get_output_topic(configuration, "server")
        ),
        "RE_Ingest.log": SourceConfiguration(
            CompositeEventCreator()
            .add_source_parser(
                DictEventCreator(
                    Metadata([
                        StringField("started_script"),
                        ConfigurableTimestampField("timestamp", None, timezone_name,
                                                   timezones_priority, "@timestamp",
                                                   use_smart_parsing=True),
                        StringField("message"),
                        StringField("finished_script"),
                        ConfigurableTimestampField("finished_time", None, timezone_name,
                                                   timezones_priority,
                                                   use_smart_parsing=True)
                    ]),
                    RegexpMatchesParser(
                        r"Started\s+?(?P<started_script>.*?\.sh)\s+?"
                        r"(?P<timestamp>\w+?\s+?\w+?\s+?\d{1,2}\s+?\d{2}:\d{2}:\d{2}\s+?\w+?\s+?\d{4})"
                        r"(?P<message>(?:.|\s)*)Finished\s+?(?P<finished_script>.*?\.sh)\s+?"
                        r"(?P<finished_time>\w+?\s+?\w+?\s+?\d{1,2}\s+?\d{2}:\d{2}:\d{2}\s+?\w+?\s+?\d{4}).*"
                    )
                )
            )
            .add_intermediate_result_parser(duration_event_creator),
            Utils.get_output_topic(configuration, "reingest")
        )
    })


def duration_update(started_script, finished_script, finished_time, timestamp):
    """
    if started script equals finished script duration is calculated
    :param started_script
    :param finished_script
    :param finished_time
    :param timestamp
    :return: duration
    ":exception: ParsingException
    """
    if started_script == finished_script:
        return abs(finished_time - timestamp).seconds
    else:
        raise ParsingException("Message contains different started and finished scripts")


if __name__ == "__main__":
    configuration = Utils.load_config(sys.argv[:])
    KafkaPipeline(
        configuration,
        LogParsingProcessor(configuration, create_event_creators(configuration))
    ).start()
