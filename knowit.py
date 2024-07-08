from os import walk, path

from note import Note


class Knowit():
    def __init__(self):
        self.cwd = "~/notes"
        self.notes = self.parse_notes()

    def parse_notes(self):
        notes = []
        for root, dir, files in walk(path.expanduser(self.cwd)):
            for f in files:
                file_path = path.join(root, f)
                notes.append(Note(file_path))
        return notes

    def get_tags(self):
        all_tags = []

        [all_tags.extend(note.tags) for note in self.notes]

        all_tags = list(set(all_tags))

        return all_tags


def main():
    try:
        knowit = Knowit()
        print(knowit.get_tags())
    except:
        import traceback
        print(traceback.format_exc())

if __name__=="__main__":
    main()
