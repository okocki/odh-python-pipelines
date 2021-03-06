"""
    Module for Event creator that can aggregate fields after parsing
"""
from inspect import getargspec

from common.log_parsing.dict_event_creator.event_creator import EventCreator


class MutateEventCreator(EventCreator):
    """
    Event creator that aggregates fields using specified aggregate functions
    """

    def __init__(self, metadata=None, fields_mappings=None):
        """
        Creates event creator
        :param fields_mappings: list of FieldsMappings
        """
        for fields_mapping in fields_mappings:
            if not callable(fields_mapping.agg_func) or len(getargspec(fields_mapping.agg_func).args) != len(
                    fields_mapping.get_fields_to_aggregate()):
                raise ValueError(
                    "Aggregate function must take same arguments count as "
                    "fields_to_aggregate count and produce single argument!")

        self.__fields_mappings = fields_mappings
        self.__metadata = metadata
        EventCreator.__init__(self, metadata, None)

    def _create_with_context(self, row, context):
        result = {}
        for fields_mapping in self.__fields_mappings:
            values_to_agg = [row[x] for x in fields_mapping.get_fields_to_aggregate()]
            result_value = fields_mapping.agg_func(*values_to_agg)
            if fields_mapping.get_remove_intermediate_fields():
                for field in fields_mapping.get_fields_to_aggregate():
                    del row[field]
            if self._metadata and self._metadata.get_field_by_name(fields_mapping.get_result_field()):
                result.update({
                    self._metadata.get_field_by_name(fields_mapping.get_result_field()).get_output_name():
                    self._metadata.get_field_by_name(fields_mapping.get_result_field()).get_value(
                        result_value, context)})
            else:
                result.update({fields_mapping.get_result_field(): result_value})
        return result

    def contains_fields_to_parse(self, row):
        fields = [x.get_fields_to_aggregate() for x in self.__fields_mappings]
        return set(reduce(lambda x, y: x + y,
                          fields)).issubset(set(row.keys()))


def concat_strings(x, y):
    """
    Concat two strings
    """
    return x + " " + y


class FieldsMapping(object):
    """
    Case class that contain list of fields to aggregate,
    result field, aggregation function and boolean flag that indicates removing of intermediate fields
    """

    def __init__(self, fields_to_aggregate, result_field, agg_func=concat_strings,
                 remove_intermediate_fields=False):
        if (not fields_to_aggregate and not isinstance(fields_to_aggregate, list)) \
                or (not result_field and isinstance(result_field, str)):
            raise ValueError("Expected not None arguments")
        self.__fields_to_aggregate = fields_to_aggregate
        self.__result_field = result_field
        self.__remove_intermediate_fields = remove_intermediate_fields
        self.agg_func = agg_func

    def get_fields_to_aggregate(self):
        return self.__fields_to_aggregate

    def get_result_field(self):
        return self.__result_field

    def get_remove_intermediate_fields(self):
        return self.__remove_intermediate_fields

