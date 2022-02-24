import re
from datetime import datetime

import dateparser
from pydantic import BaseModel

date_pattern = re.compile(
    r'at\s(?P<time>[\d\:]+\s(am|pm))\son\s(?P<date>[\d]{1,2}\s[\w]+\s[\d]{4})'
)


class Image(BaseModel):
    link: str
    sent_at: datetime

    @classmethod
    def from_link_and_header(cls, link: str, header: str) -> 'Image':
        result = date_pattern.search(header)

        result_dict = result.groupdict()
        return cls(
            link=link,
            sent_at=dateparser.parse(f"{result_dict['date']} {result_dict['time']}"),
        )
