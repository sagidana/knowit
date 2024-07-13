from subprocess import Popen, PIPE, DEVNULL
from os import walk, path, environ, remove
from sys import stdin, stdout, stderr
from datetime import datetime
from requests import post
from time import sleep
import traceback
import argparse

from note import Note


def vim(path, command=""):
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

def rg_fzf(locations=["~/notes"]):
    rg_prefix = "rg --column --line-number --no-heading --color=always --smart-case "
    rg_suffix = f" {' '.join(locations)}"
    initial_query = "\"\""
    cmd = ["fzf"]
    env = environ.copy()
    fzf_options = "--ansi "
    fzf_options += "--delimiter : "
    fzf_options += "--disabled "
    fzf_options += f"--query \"{initial_query}\" "
    fzf_options += f"--bind \"change:reload:sleep 0.1; {rg_prefix} {{q}} {rg_suffix} || true\" "
    fzf_options += "--bind 'ctrl-k:preview-up' "
    fzf_options += "--bind 'ctrl-j:preview-down' "
    fzf_options += "--bind 'ctrl-u:preview-half-page-up' "
    fzf_options += "--bind 'ctrl-d:preview-half-page-down' "
    fzf_options += "--preview-window 'down,80%,+{2}-/2' "
    fzf_options += "--preview 'bat --style=auto --color=always -H {2} {1}' "

    env["FZF_DEFAULT_COMMAND"] = f"{rg_prefix} {initial_query} {rg_suffix}"
    env["INITIAL_QUERY"] = initial_query
    env["FZF_DEFAULT_OPTS"] = fzf_options
    p = Popen(cmd,
              stdin=stdin,
              stdout=PIPE,
              stderr=stderr,
              env=env)
    output, errors = p.communicate()
    return output.decode('utf-8').strip()

def fzf(options, selected):
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
        fzf_options = "--listen 6266 "
        fzf_options += "--sync "
        fzf_options += "--border rounded "
        fzf_options += f"--border-label \"{'|'.join(selected)}\" "
        fzf_options += "--bind 'ctrl-z:toggle-preview' "
        fzf_options += "--bind 'ctrl-k:preview-up' "
        fzf_options += "--bind 'ctrl-j:preview-down' "
        fzf_options += "--bind 'ctrl-u:preview-half-page-up' "
        fzf_options += "--bind 'ctrl-d:preview-half-page-down' "
        fzf_options += "--bind 'esc:clear-query' "
        # fzf_options += "--bind 'change:refresh-preview' "
        fzf_options += "--bind 'tab:toggle+clear-query' "
        fzf_options += f"--bind 'tab:+reload(python {path.abspath(__file__)} -a fzf_reload -t {{}})' "
        fzf_options += "--tiebreak=index "
        fzf_options += "--preview-window 'down,80%' "
        fzf_options += f"--preview 'python {path.abspath(__file__)} -a fzf_preview --color -t {{}}'"

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
                except Exception as e:
                    # print(f"[!] failed to parse note: {e}")
                    continue
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
        lines.extend([
                f"{' '.join(['#'+tag for tag in tags])}\n",
            ])

        #TODO: use creation time to control order?
        for note in self.notes:
            if not set(tags).issubset(set(note.tags)): continue
            lines.extend(["\n", "---\n"])

            map[note.path] = [len(lines) + 1]

            # first line of note (for folding next)
            note_content = open(note.path).readlines()
            lines.extend([
                            f"{note.path}\n",
                            "\n",
                            "---\n",
                          ])
            lines.extend(note_content.copy())
            # last line of note (for folding next)
            map[note.path].append(len(lines))
            prev_existed = True

        file_path = "/tmp/knowit.md"
        open(file_path, "w+").write("".join(lines))

        vim_script = "set foldmethod=manual\n\n"
        vim_script += f"execute \"normal! zE\"\n" # remove all folds
        for note_path in map:
            start = map[note_path][0]
            end = map[note_path][1]
            # configure folds per note
            vim_script += f"execute \"normal! :{start},{end}fold\\<cr>\"\n"
            print(f"execute \"normal! :{start},{end}fold\\<cr>\"\n")

        vim_script += f"execute \"normal! zR\"\n" # open folds

        vim_script_path = "/tmp/knowit.vim"
        open(vim_script_path, "w+").write("".join(vim_script))

        rc = vim(file_path, f":source {vim_script_path}")

        remove(file_path)
        remove(vim_script_path)

    def select(self):
        """view to search the notes using tags"""
        selected = self.args.tags
        tags = self.get_tags()
        selected_tags = fzf(tags, selected=selected)
        if len(selected_tags) == 0: return

        # TODO: create vim view with folds and markdown
        self.vim_view(selected_tags)

    def grep(self):
        """view to search the notes using grep"""

        locations = []
        tags = self.args.tags
        if not tags: locations.append("~/notes") # search all
        else:
            for note in self.notes:
                if not set(tags).issubset(set(note.tags)): continue
                locations.append(note.path)

        result = rg_fzf(locations)
        if not result: return

        file_path = result.split(":")[0]
        file_line = result.split(":")[1]
        vim(file_path, file_line)


    def tag(self):
        """view to select tags for newly created note"""
        pass

    def view_sync(self):
        """
        sync the view file against the notes
        - if notes were changed inside the view - update the notes.
            - if there are conflicts do not.
        - if new notes were added, add them to the notes
        - if new notes were added externally that fits the view (based
          on the tags of the view), append them to the end of the view.
        """
        if not self.args.view_path:
            print("'view_sync' action need --view-path option to be set.")
            return
        pass

    def fzf_reload(self):
        selected = self.args.tags
        assert len(selected) == 1
        selected = selected[0]
        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        tags = []
        if fzf_label:
            tags = fzf_label.split('|')

        # toggle
        if selected in tags:
            tags.remove(selected)
        elif selected != "":
            tags.append(selected)

        relevant = tags.copy()
        for note in self.notes:
            if not set(tags).issubset(set(note.tags)): continue
            relevant.extend(note.tags)
        relevant = list(set(relevant))

        for tag in relevant: print(tag, flush=True)

        fzf_label = "|".join(tags)

        # we need to re-select the tags for fzf to continue from where we stopped
        post("http://localhost:6266/", data=f"change-border-label({fzf_label})")

    def fzf_preview(self):
        selected = self.args.tags
        assert len(selected) == 1
        selected = selected[0]
        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        tags = []
        if fzf_label:
            tags = fzf_label.split('|')

        if not fzf_query or selected:
            tags.append(selected)

        content = ""
        prev_existed = False
        relevant_notes = []
        relevant_tags = tags.copy()
        #TODO: use creation time to control order?
        for note in self.notes:
            if not set(tags).issubset(set(note.tags)): continue
            relevant_notes.append(note)
            relevant_tags.extend(note.tags)
        relevant_tags = list(set(relevant_tags))

        open('/tmp/knowit.log', 'a+').write(f"tags: {tags}\n")
        open('/tmp/knowit.log', 'a+').write(f"relevant_tags: {relevant_tags}\n")

        need_to_grep = True
        for tag in relevant_tags:
            if fzf_query in tag:
                need_to_grep = False
                break

        if need_to_grep:
            open('/tmp/knowit.log', 'a+').write(f"TODO: grepping...\n")
            print("TODO: grepping...")
            return

        for note in relevant_notes:
            if prev_existed: content += "\n---\n\n"

            if len(note.content) > 4:
                content += ''.join(note.content[:4])
            else:
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
                                    "tag",
                                    "grep",
                                    "fzf_reload",
                                    "fzf_preview",
                                    "view_sync",
                                ],
                        help="the action to be perfomed")
    parser.add_argument('-t',
                        '--tags',
                        nargs='+',
                        default=[],
                        help="list of tags to perform action on.")
    parser.add_argument('--query',
                        help="this is the fzf query in case of fzf_reload action")
    parser.add_argument('--color',
                        action="store_true",
                        help="syntax highlight the results")
    parser.add_argument('--view-path',
                        help="the path to the view (vim) file with view into notes")

    args = parser.parse_args()
    knowit = Knowit(args)

    if args.action == "create":
        knowit.create_note()
    if args.action == "select":
        knowit.select()
    if args.action == "fzf_preview":
        knowit.fzf_preview()
    if args.action == "grep":
        knowit.grep()
    if args.action == "fzf_reload":
        knowit.fzf_reload()
    if args.action == "view_sync":
        knowit.view_sync()
    if args.action == "tag":
        knowit.tag()


if __name__=="__main__":
    try:
        main()
    except:
        print(traceback.format_exc())
