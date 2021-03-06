import unittest

from datetime import datetime

from dateutil.tz import tzoffset

from common.log_parsing.timezone_metadata import *
from common.log_parsing.timezone_metadata import _get_available_timezones


class ConfigurableTimestampTestCase(unittest.TestCase):

    _winter_date_utc1 = datetime(2017, 12, 28, 13, 39, 11, 238000).replace(tzinfo=tzoffset(None, 3600))
    _winter_date_utc2 = datetime(2017, 12, 28, 13, 39, 11, 238000).replace(tzinfo=tzoffset(None, 7200))

    _winter_date_string_tz = "2017-12-28 13:39:11.238000 +0200"
    _winter_date_string = "2017-12-28 13:39:11.238000"

    _summer_date = datetime(2017, 7, 28, 13, 39, 11, 238000).replace(tzinfo=tzoffset(None, 7200))
    _summer_date_string_tz = "2017-07-28 13:39:11.238000 +0200"

    _ambiguous_date = datetime(2016, 10, 30, 2, 0, 0, 0).replace(tzinfo=timezones["Europe/Amsterdam"])
    _ambiguous_date_string = "2016-10-30 2:00:00"

    def test_get_available_timezones(self):
        zonemap = {}
        for zone in _get_available_timezones("test/unit/resources/timezones"):
            zonemap[zone[0]] = zone[1].replace("\\", "/")

        self.assertEquals(4, len(zonemap))
        self.assertEquals("test/unit/resources/timezones/America/Adak", zonemap["America/Adak"])
        self.assertEquals("test/unit/resources/timezones/America/Argentina/Buenos_Aires", zonemap["America/Argentina/Buenos_Aires"])
        self.assertEquals("test/unit/resources/timezones/Europe/Amsterdam", zonemap["Europe/Amsterdam"])
        self.assertEquals("test/unit/resources/timezones/CET", zonemap["CET"])

    def test_load_timezones(self):
        timezone_map = load_timezones("test/unit/resources/timezones")

        self.assertEquals(4, len(timezone_map))


    def test_load_timezones_main(self):
        self.assertTrue(len(timezones) > 0)

    def test_configurable_timestamp_field_dic_override_winter(self):
        field = ConfigurableTimestampField("datetime", "%Y-%m-%d %H:%M:%S.%f", "Europe/Amsterdam", "dic",
                                           include_timezone=True)
        parsed_date = field.get_value(self._winter_date_string_tz)

        self.assertEquals(self._winter_date_utc1, parsed_date)

    def test_configurable_timestamp_field_dic_override_summer(self):
        field = ConfigurableTimestampField("datetime", "%Y-%m-%d %H:%M:%S.%f", "Europe/Amsterdam", "dic",
                                           include_timezone=True)
        parsed_date = field.get_value(self._summer_date_string_tz)

        self.assertEquals(self._summer_date, parsed_date)

    def test_configurable_timestamp_field_dic_not_override(self):
        field = ConfigurableTimestampField("datetime", "%Y-%m-%d %H:%M:%S.%f", "Europe/Amsterdam", "dic")
        parsed_date = field.get_value(self._winter_date_string)

        self.assertEquals(self._winter_date_utc1, parsed_date)

    def test_configurable_timestamp_field_idc(self):
        field = ConfigurableTimestampField("datetime", "%Y-%m-%d %H:%M:%S.%f", "Europe/Amsterdam", "idc",
                                           include_timezone=True)
        parsed_date = field.get_value(self._winter_date_string_tz)

        self.assertEquals(self._winter_date_utc2, parsed_date)


    def test_configurable_timestamp_field_cdi(self):
        field = ConfigurableTimestampField("datetime", "%Y-%m-%d %H:%M:%S.%f", "UTC+1", "cdi",
                                           include_timezone=True)
        context = {CONTEXT_TIMEZONE: "Europe/Amsterdam"}

        parsed_date = field.get_value(self._winter_date_string_tz, context)

        self.assertEquals(self._winter_date_utc1, parsed_date)

    def test_configurable_timestamp_field_bad_timezone(self):
        field = ConfigurableTimestampField("datetime", "%Y-%m-%d %H:%M:%S.%f", "Europe/Amsterdam1", "dic",
                                           include_timezone=True)
        parsed_date = field.get_value(self._winter_date_string_tz)

        self.assertEquals(self._winter_date_utc2, parsed_date)

    def test_ambiguous_date_covertion(self):
        field = ConfigurableTimestampField("datetime", None, "Europe/Amsterdam", "idc", use_smart_parsing=True)
        parsed_date = field.get_value(self._ambiguous_date_string)
        ambiguous = timezones["Europe/Amsterdam"].is_ambiguous(parsed_date)

        self.assertEquals(self._ambiguous_date, parsed_date)

    def test_load_timezones_from_main_resources(self):
        loaded_timezones = load_timezones("resources/timezones")
        self.assertTrue(len(loaded_timezones) > 0)

if __name__ == '__main__':
    unittest.main()
