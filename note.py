from datetime import datetime
import re


class Note():
    def __init__(self,
                 path,
                 timestamp,
                 tags,
                 links,
                 content):
        self.path = path
        self.timestamp = timestamp
        self.tags = tags
        self.links = links
        self.content = content

    def dump(self):
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        to_dump = f"[{timestamp_str}]"
        for tag in self.tags: to_dump += f" #{tag}"
        to_dump += "\n"
        to_dump += "---" + "\n"
        to_dump += "".join(self.content)
        open(self.path, 'w').write(to_dump)

    @staticmethod
    def parse(path):
        lines = open(path, 'r').readlines()
        assert len(lines) > 2

        m = re.match(r"^\[(?P<date>\d\d\d\d-\d\d\-\d\d\ \d\d:\d\d:\d\d)\]\s+(?P<tags>(\#\w+\s+)*)?$", lines[0])
        assert m is not None

        timestamp = datetime.strptime(m.group('date'), "%Y-%m-%d %H:%M:%S")
        tags = m.group('tags').strip().split('#')[1:]
        tags = [tag.strip() for tag in tags]

        m = re.match(r"^---$", lines[1])
        assert m is not None

        content = lines[2:]
        links = []
        for line in content:
            m = re.match(r"^.*\[(?P<from>=>)?(?P<link>\w{10})(?P<to>=>)?\].*$", line)
            if m is None: continue
            link_id = m.group('link')
            link_from = m.group('from')
            link_to = m.group('to')
            links.append((link_from is not None, link_id, link_to is not None))

        return Note(path, timestamp, tags, links, content)
