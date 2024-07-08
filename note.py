from datetime import datetime
import re


class Note():
    def __init__(self, path):
        lines = open(path, 'r').readlines()
        assert len(lines) > 2

        m = re.match(r"^\[(?P<date>\d\d\d\d-\d\d\-\d\d\ \d\d:\d\d:\d\d)\]\s(?P<tags>(\#\w+\s)*)?$", lines[0])
        assert m is not None

        self.timestamp = datetime.strptime(m.group('date'), "%Y-%m-%d %H:%M:%S")
        self.tags = m.group('tags').strip().split('#')[1:]

        m = re.match(r"^={80}$", lines[1])
        assert m is not None

        self.note = lines[2:]
        self.links = []
