from subprocess import Popen, PIPE, DEVNULL
from datetime import datetime
from sys import stdin, stdout, stderr
from os import walk, path, environ
import traceback
import argparse

from note import Note


def gotovim(path, content):
    try:
        cmd = ["nvim", path, "-c", f"normal i{content}"]
        env = environ.copy()
        p = Popen(cmd,
                  stdin=stdin,
                  stdout=stdout,
                  env=env)
        output, errors = p.communicate()
    except Exception as e: print(f"traceback: {traceback.format_exc()}")

def tags_selection_preview():
    import sys
    from subprocess import run
    if len(sys.argv) < 2: return
    tags = sys.argv[1:]

    cmd = ["python3",
           "/home/s/github/knowit/knowit.py",
           "-a", "view",
           "-t"]
    cmd.extend(tags)
    result = run(cmd, capture_output=True, text=True)
    print(result.stdout)

def fzf(options, preview_cb):
    import inspect
    """
    This is so cool, fzf print out to stderr the fuzzing options,
    and only the chosen result spit to the stdout.. this enables scripts like
    this to work out of the box, no redirection of the stderr is need - and
    only the result is redirected to our pipe (which contain the result)
    FZF - good job :)
    NOTE: influenced by https://jeskin.net/blog/grep-fzf-clp/
    NOTE: https://github.com/jpe90/clp is needed to be installed!
    """
    try:
        source = inspect.getsource(preview_cb)
        source += "\n"
        source += "from inspect import getmembers, isfunction\n"
        source += "from sys import modules\n"
        source += "\n"
        source += "for _,obj in getmembers(modules[__name__]):\n"
        source += "    if not isfunction(obj): continue\n"
        source += "    if not isfunction(obj): continue\n"
        source += "    if 'preview' not in obj.__name__: continue\n"
        source += "    obj()\n"
        open("/tmp/preview.py", "w+").write(source)

        fzf_options = "--bind 'ctrl-z:toggle-preview' "
        fzf_options += "--bind 'ctrl-u:preview-up' "
        fzf_options += "--bind 'ctrl-d:preview-down' "
        fzf_options += "--tiebreak=index "
        # fzf_options += "--preview-window '90%' "
        fzf_options += "--preview-window 'up,80%' "
        fzf_options += "--multi " # mutli selection of options
        # fzf_options += "--preview 'python /tmp/preview.py {+} | bat -l md --style=full --color=always'"
        fzf_options += "--preview 'python /tmp/preview.py {+}'"

        env = environ.copy()
        env["FZF_DEFAULT_OPTS"] = fzf_options
        p = Popen(["fzf"],
                  stdin=PIPE,
                  stdout=PIPE,
                  stderr=stderr,
                  env=env)
        # write the options to stdin before launching the pocess with communicate()
        p.stdin.write("\n".join(options).encode())

        output, errors = p.communicate()

        results = output.decode('utf-8').strip()
        return results.splitlines()
    except Exception as e: print(f"traceback: {traceback.format_exc()}")

def bat(content):
    """
    Calling bat for syntax highlighting
    """
    try:
        env = environ.copy()
        p = Popen(["bat",
                   "-l", "md", # markdown language
                   "--style=auto",
                   "--color=always",
                   ],
                  stdin=PIPE,
                  stdout=PIPE,
                  stderr=stderr,
                  env=env)
        # write the options to stdin before launching the pocess with communicate()
        p.stdin.write(content.encode())
        output, errors = p.communicate()
        return output

    except Exception as e: print(f"traceback: {traceback.format_exc()}")

class Knowit():
    def __init__(self, args=None):
        self.cwd = path.expanduser("~/notes")
        self.notes = self.parse_notes()
        self.args = args

    def parse_notes(self):
        notes = []
        for root, dir, files in walk(self.cwd):
            for f in files:
                file_path = path.join(root, f)
                try:
                    note = Note.parse(file_path)
                    notes.append(note)
                except: continue
        return notes

    def get_tags(self):
        all_tags = []

        [all_tags.extend(note.tags) for note in self.notes]

        all_tags = list(set(all_tags))

        return all_tags

    def get_links(self):
        all_links = []

        for note in self.notes:
            for link in note.links:
                # link_from = link[0]
                link_id = link[1]
                # link_to = link[2]
                all_links.append(link_id)
        all_links = list(set(all_links))
        return all_links

    def create_note(self):
        i = 0
        while path.exists(path.join(self.cwd, f"{i}.md")): i += 1
        note_path = path.join(self.cwd, f"{i}.md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"[{timestamp}]\n"
        content += "="*80 + "\n"

        gotovim(note_path, content)

    def select_tags(self):
        tags = self.get_tags()
        selected_tags = fzf(tags, tags_selection_preview)

        # TODO: create vim view with folds and markdown
        print(f"selected_tags: {selected_tags}")

    def view(self):
        if len(self.args.tags) == 0: return

        content = ""
        for note in self.notes:
            if not set(self.args.tags).issubset(set(note.tags)): continue
            content += ''.join(note.content)
        stdout.buffer.write(bat(content))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a',
                        '--action',
                        choices=[
                                    "create",
                                    "select",
                                    "view",
                                ],
                        help="the action to be perfomed")
    parser.add_argument('-t',
                        '--tags',
                        nargs='+',
                        default=[],
                        help="list of tags to perform action on.")

    args = parser.parse_args()
    knowit = Knowit(args)

    if args.action == "create":
        knowit.create_note()
    if args.action == "select":
        knowit.select_tags()
    if args.action == "view":
        knowit.view()

    # knowit.notes[0].dump()
    # print(knowit.get_tags())

if __name__=="__main__":
    try:
        main()
    except:
        print(traceback.format_exc())
