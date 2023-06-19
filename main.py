import dataclasses
import datetime
import re

import dateutil.relativedelta
import humanize


class TimestampExtractor:
    def __init__(self):
        self.patterns = []

    def add_pattern(self, pattern):
        self.patterns.append(pattern)

    def extract_timestamp(self, filename):
        for pattern in self.patterns:
            matches = pattern.search(filename)
            if matches:
                year = int(matches.group("year"))
                month = int(matches.group("month"))
                day = int(matches.group("day"))
                hour = int(matches.group("hour"))
                minute = int(matches.group("minute"))
                second = (
                    int(matches.group("second"))
                    if "second" in matches.groupdict()
                    else 0
                )
                offset = (
                    int(matches.group("offset"))
                    if "offset" in matches.groupdict()
                    else 0
                )

                gmt_offset = datetime.timedelta(hours=offset)

                return (
                    datetime.datetime(year, month, day, hour, minute, second)
                    + gmt_offset
                )
        return None


@dataclasses.dataclass
class Record:
    size: int
    filename: str
    timestamp: datetime.datetime

    def formatted_size(self):
        return humanize.naturalsize(self.size, binary=True)

    def get_age(self):
        current_time = datetime.datetime.now()
        age_timestamp = self.timestamp
        age = dateutil.relativedelta.relativedelta(current_time, age_timestamp)
        return self.format_relativedelta(age)

    @staticmethod
    def format_relativedelta(rd):
        formatted_age = ""
        if rd.years:
            formatted_age += f"{rd.years}y"
        if rd.months:
            formatted_age += f"{rd.months}mo"
        if rd.days:
            formatted_age += f"{rd.days}d"
        if rd.hours:
            formatted_age += f"{rd.hours}h"
        return formatted_age.rjust(15)

    def __str__(self):
        iso_timestamp = self.timestamp.isoformat() if self.timestamp else ""
        return f"{self.get_age().rjust(7)} {self.formatted_size().rjust(10)} {iso_timestamp} {self.filename}"  # noqa: E501


# Create an instance of TimestampExtractor
timestamp_extractor = TimestampExtractor()

# Define the existing regex patterns and add them to the TimestampExtractor
existing_patterns = [
    re.compile(
        r"""
        (
            # 2021-04-22 at 11_01 GMT-7
            (?P<year>\d{4})-
            (?P<month>\d{2})-
            (?P<day>\d{2})
            \s
            at
            \s
            (?P<hour>\d{2})
            _
            (?P<minute>\d{2})
            \s
            GMT(?P<offset>-\d+)
        )
        """,
        re.VERBOSE,
    ),
    re.compile(
        r"""
        (
            # GMT20220909-181023
            (?P<year>\d{4})
            (?P<month>\d{2})
            (?P<day>\d{2})
            [_-]
            (?P<hour>\d{2})
            (?P<minute>\d{2})
            (?P<second>\d{2})
        )
        """,
        re.VERBOSE,
    ),
    re.compile(
        r"""
        (
            # 2022-05-29 17:52:23
            (?P<year>\d{4})
            -
            (?P<month>\d{2})
            -
            (?P<day>\d{2})
            [\s_-]
            (?P<hour>\d{2})
            :
            (?P<minute>\d{2})
            :
            (?P<second>\d{2})
        )
        """,
        re.VERBOSE,
    ),
]

for pattern in existing_patterns:
    timestamp_extractor.add_pattern(pattern)

# Add a new regex pattern for the additional timestamp format
new_pattern = re.compile(
    r"""
    (
        # New timestamp format
        # Modify this pattern according to the new format
        # (?P<new_group>\d{4}-\d{2}-\d{2})
        # ...
    )
    """,
    re.VERBOSE,
)

# timestamp_extractor.add_pattern(new_pattern)

with open("list.txt", "r") as file:
    lines = file.readlines()

records = []
for line in lines:
    parts = line.strip().split()
    s3_timestamp = " ".join(parts[:2])
    size = int(parts[2])
    filename = " ".join(parts[3:])
    timestamp = timestamp_extractor.extract_timestamp(
        filename
    ) or timestamp_extractor.extract_timestamp(s3_timestamp)
    record = Record(size, filename, timestamp)
    records.append(record)


sorted_by_size = sorted(records, key=lambda r: r.size, reverse=True)
print("Sorted by File Size:")
for record in sorted_by_size:
    print(record)

# Sort records by timestamp
sorted_by_timestamp = sorted(
    records, key=lambda r: (r.timestamp or datetime.datetime.min), reverse=False
)
print("Sorted by Timestamp:")
for record in sorted_by_timestamp:
    print(record)
