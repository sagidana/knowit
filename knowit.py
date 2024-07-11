from subprocess import Popen, PIPE, DEVNULL
from datetime import datetime
from sys import stdin, stdout, stderr
from os import walk, path, environ, remove
import traceback
import argparse

from note import Note


def vim(path, command):
    try:
        cmd = ["nvim", path, "-c", command]
        env = environ.copy()
        p = Popen(cmd,
                  stdin=stdin,
                  stdout=stdout,
                  env=env)
        output, errors = p.communicate()
        return p.returncode
    except Exception as e: print(f"traceback: {traceback.format_exc()}")

def tags_selection_preview():
    import sys
    from subprocess import run
    if len(sys.argv) < 2: return
    tags = sys.argv[1:]

    cmd = ["python3",
           "/home/s/github/knowit/knowit.py",
           "-a", "view",
           "--color",
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
        fzf_options += "--bind 'ctrl-k:preview-up' "
        fzf_options += "--bind 'ctrl-j:preview-down' "
        fzf_options += "--bind 'ctrl-u:preview-half-page-up' "
        fzf_options += "--bind 'ctrl-d:preview-half-page-down' "
        fzf_options += "--bind 'esc:clear-query' "
        fzf_options += "--tiebreak=index "
        fzf_options += "--preview-window 'up,80%' "
        fzf_options += "--multi " # mutli selection of options
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
    finally:
        remove("/tmp/preview.py")

def bat(content):
    """
    Calling 'bat' for syntax highlighting
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
        content += "---" + "\n"

        vim(note_path, f"normal i{content}")

    def vim_view(self, tags):
        lines = []
        map = {}

        prev_existed = False

        #TODO: use creation time to control order?
        for note in self.notes:
            if not set(tags).issubset(set(note.tags)): continue
            if prev_existed:
                lines.extend(["\n",
                              "---\n",
                              "\n"])

            # first line of note (for folding next)
            map[note.path] = [len(lines) - (1 if prev_existed else 0)]
            lines.extend(note.content.copy())
            # last line of note (for folding next)
            map[note.path].append(len(lines))
            prev_existed = True

        before_file_path = "/tmp/knowit_before.md"
        after_file_path = "/tmp/knowit_after.md"

        open(before_file_path, "w+").write("".join(lines))
        open(after_file_path, "w+").write("".join(lines))

        vim_script = "set foldmethod=manual\n\n"
        for note_path in map:
            start = map[note_path][0]
            end = map[note_path][1]
            print(f"start: {start}, end: {end}")
            vim_script += f"execute \"normal! :{start},{end}fold\\<cr>\"\n"

        vim_script_path = "/tmp/knowit.vim"
        open(vim_script_path, "w+").write("".join(vim_script))

        rc = vim(after_file_path, f":source {vim_script_path}")

        # TODO: diff the changed file with the original and update notes!

        remove(file_path)
        remove(vim_script_path)

    def select(self):
        tags = self.get_tags()
        selected_tags = fzf(tags, tags_selection_preview)
        if len(selected_tags) == 0: return

        # TODO: create vim view with folds and markdown
        print(f"selected_tags: {selected_tags}")
        self.vim_view(selected_tags)

    def view(self):
        if len(self.args.tags) == 0: return

        content = ""
        prev_existed = False
        #TODO: use creation time to control order?
        for note in self.notes:
            if not set(self.args.tags).issubset(set(note.tags)): continue
            if prev_existed: content += "\n---\n\n"
            content += ''.join(note.content)
            prev_existed = True

        content = bat(content) if self.args.color else content.encode()
        stdout.buffer.write(content)


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
    parser.add_argument('--color',
                        action="store_true",
                        help="syntax highlight the results")

    args = parser.parse_args()
    knowit = Knowit(args)

    if args.action == "create":
        knowit.create_note()
    if args.action == "select":
        knowit.select()
    if args.action == "view":
        knowit.view()

    # knowit.notes[0].dump()
    # print(knowit.get_tags())

if __name__=="__main__":
    try:
        main()
    except:
        print(traceback.format_exc())
