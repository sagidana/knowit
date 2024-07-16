from subprocess import Popen, PIPE, DEVNULL
from os import walk, path, environ, remove, isatty, ctermid
from sys import stdin, stdout, stderr
from datetime import datetime
from requests import post
from time import sleep
import traceback
import argparse
import re

from note import Note

def log(message):
    with open('/tmp/knowit.log', 'a+') as f:
        f.write(f"{message}\n")

def vim(path, commands=[]):
    try:
        cmd = ["nvim", path]
        for command in commands:
            cmd.extend(["-c", command])

        # fzf lost stdout/stdin so we retrieve them
        _stdin = open(ctermid(), 'rb')
        _stdout = open(ctermid(), 'w')

        env = environ.copy()
        # fzf keeps some of its environment variables, remove them to keep
        # clean operation
        if "FZF_DEFAULT_COMMAND" in env: del env["FZF_DEFAULT_COMMAND"]
        if "INITIAL_QUERY" in env: del env["INITIAL_QUERY"]
        if "FZF_DEFAULT_OPTS" in env: del env["FZF_DEFAULT_OPTS"]

        p = Popen(cmd,
                  stdin=_stdin,
                  stdout=_stdout,
                  stderr=_stdout,
                  env=env)

        output, errors = p.communicate()
        return p.returncode
    except Exception as e:
        open('/tmp/knowit.log', 'a+').write(f"traceback: {traceback.format_exc()}")
        # print(f"traceback: {traceback.format_exc()}")

def rg_fzf(locations=["~/notes"]):
    rg_prefix = "rg -H --column --line-number --no-heading --color=always --smart-case "
    rg_suffix = f" {' '.join(locations)}"

    initial_query = "\"\""
    cmd = ["fzf"]
    env = environ.copy()
    fzf_options = "--ansi "
    fzf_options += "--delimiter : "
    fzf_options += "--disabled "
    fzf_options += f"--query {initial_query} "
    fzf_options += f"--bind \"change:reload:{rg_prefix} {{q}} {rg_suffix} || true\" "
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

def tag_fzf(tags,
            selected,
            on_enter=f"python {path.abspath(__file__)} -a view -t {{}}"):
    """
    This is so cool, fzf print out to stderr the fuzzing options,
    and only the chosen result spit to the stdout.. this enables scripts like
    this to work out of the box, no redirection of the stderr is need - and
    only the result is redirected to our pipe (which contain the result)
    FZF - good job :)
    NOTE: influenced by https://jeskin.net/blog/grep-fzf-clp/
    NOTE: https://github.com/jpe90/clp is needed to be installed!
    """

    _tags = []
    for tag, count in reversed(sorted(tags.items(), key=lambda x: x[1])):
        _tags.append(f"#{tag} [{count}]")
    tags = _tags

    fzf_options = "--listen 6266 "
    fzf_options += "--sync "
    fzf_options += "--nth ..-2 "
    fzf_options += "--layout reverse "
    fzf_options += "--border rounded "
    fzf_options += "--border-label-pos 3 "
    fzf_options += f"--border-label \"{' '.join(selected)}\" "
    fzf_options += "--bind 'ctrl-z:toggle-preview' "
    fzf_options += f"--bind 'ctrl-t:become(python {path.abspath(__file__)} -a create -t {{}})' "
    fzf_options += "--bind 'ctrl-k:preview-up' "
    fzf_options += "--bind 'ctrl-j:preview-down' "
    fzf_options += "--bind 'ctrl-u:preview-half-page-up' "
    fzf_options += "--bind 'ctrl-d:preview-half-page-down' "
    fzf_options += f"--bind 'ctrl-g:become(python {path.abspath(__file__)} -a grep -t {{}})' "
    fzf_options += "--bind 'esc:clear-query' "
    fzf_options += f"--bind 'enter:become({on_enter})' "
    fzf_options += "--bind 'tab:toggle+clear-query' "
    fzf_options += f"--bind 'tab:+reload(python {path.abspath(__file__)} -a tag_fzf_reload -t {{}})' "
    fzf_options += "--tiebreak=index "
    fzf_options += "--preview-window 'down,80%' "
    fzf_options += f"--preview 'python {path.abspath(__file__)} -a tag_fzf_preview --color -t {{}}'"

    env = environ.copy()
    env["FZF_DEFAULT_OPTS"] = fzf_options
    p = Popen(["fzf"],
              stdin=PIPE,
              stdout=PIPE,
              stderr=stderr,
              env=env)
    # write the options to stdin before launching the pocess with communicate()
    p.stdin.write("\n".join(tags).encode())

    output, errors = p.communicate()
    results = output.decode('utf-8').strip()

    return results.splitlines()

def note_fzf(tags,
            selected,
            on_enter=f"python {path.abspath(__file__)} -a view -t {{}}"):
    """
    This is so cool, fzf print out to stderr the fuzzing options,
    and only the chosen result spit to the stdout.. this enables scripts like
    this to work out of the box, no redirection of the stderr is need - and
    only the result is redirected to our pipe (which contain the result)
    FZF - good job :)
    NOTE: influenced by https://jeskin.net/blog/grep-fzf-clp/
    NOTE: https://github.com/jpe90/clp is needed to be installed!
    """

    _tags = []
    for tag, count in reversed(sorted(tags.items(), key=lambda x: x[1])):
        _tags.append(f"#{tag} [{count}]")
    tags = _tags

    fzf_options = "--listen 6266 "
    fzf_options += "--sync "
    fzf_options += "--nth ..-2 "
    fzf_options += "--layout reverse "
    fzf_options += "--border rounded "
    fzf_options += "--border-label-pos 3 "
    fzf_options += f"--border-label \"{' '.join(selected)}\" "
    fzf_options += "--bind 'ctrl-z:toggle-preview' "
    fzf_options += f"--bind 'ctrl-t:become(python {path.abspath(__file__)} -a create -t {{}})' "
    fzf_options += "--bind 'ctrl-k:preview-up' "
    fzf_options += "--bind 'ctrl-j:preview-down' "
    fzf_options += "--bind 'ctrl-u:preview-half-page-up' "
    fzf_options += "--bind 'ctrl-d:preview-half-page-down' "
    fzf_options += f"--bind 'ctrl-g:become(python {path.abspath(__file__)} -a grep -t {{}})' "
    fzf_options += "--bind 'esc:clear-query' "
    fzf_options += f"--bind 'enter:become({on_enter})' "
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
    p.stdin.write("\n".join(tags).encode())

    output, errors = p.communicate()
    results = output.decode('utf-8').strip()

    return results.splitlines()

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

        new_tags = []
        # remove the '#' if exists
        for tag in self.args.tags:
            if tag.startswith("#"):
                new_tags.append(tag[1:])
            else:
                new_tags.append(tag)
        self.args.tags = new_tags

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
        all_tags = {}

        for note in self.notes:
            for tag in note.tags:
                if tag not in all_tags: all_tags[tag] = 0
                all_tags[tag] += 1
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

    def create(self):
        i = 0
        selected = self.args.tags
        fzf_selected = ""
        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        if not selected:
            tag_fzf(self.get_tags(), selected=selected,
                    on_enter=f"python {path.abspath(__file__)} -a create -t {{}}")
            return

        # in case we in fzf context, initialize accordingly
        if "FZF_QUERY" in environ:
            assert len(selected) == 1
            fzf_selected = self.fzf_selected_parse(selected[0])
            selected = []

        if fzf_label:
            selected = ''.join(fzf_label.split()) # remove all spaces
            selected = selected.strip().split("#")
            selected = [x for x in selected if x] # remove empty strings
            fzf_selected = selected

        if fzf_query:
            selected.extend(fzf_selected)

        tags = list(set(selected))

        while path.exists(path.join(self.cwd, f"{i}.md")): i += 1
        note_path = path.join(self.cwd, f"{i}.md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"[{timestamp}]{''.join([' #'+tag for tag in tags])}\n\n"
        content += "---" + "\n"

        vim(note_path, [f"normal i{content}"])

    def view(self):
        """open view of relevant tags in vim"""
        tags = self.args.tags
        fzf_selected = ""
        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        # in case we in fzf context, initialize accordingly
        if "FZF_QUERY" in environ:
            assert len(tags) == 1
            fzf_selected = self.fzf_selected_parse(tags[0])
            tags = []

        if fzf_label:
            tags = ''.join(fzf_label.split()) # remove all spaces
            tags = tags.strip().split("#")
            tags = [x for x in tags if x] # remove empty strings

        if fzf_query:
            tags.extend(fzf_selected)
        elif len(tags) == 0 and fzf_selected:
            tags.extend(fzf_selected)

        tags = list(set(tags))
        lines = []
        map = {}

        prev_existed = False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"[{timestamp}]{''.join([' #'+tag for tag in tags])}\n")

        relevant_notes = []
        for note in self.notes:
            if not set(tags).issubset(set(note.tags)): continue
            relevant_notes.append(note)

        # order notes by time of creation
        relevant_notes.sort(key=lambda x:x.timestamp)

        # if one note, open directly.
        if len(relevant_notes) == 1:
            vim(relevant_notes[0].path)
            return

        for note in relevant_notes:
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

        i = 0
        while path.exists(path.join(self.cwd, f"{i}.md")): i += 1
        file_path = path.join(self.cwd, f"{i}.md")

        vim_script = f"set nopaste\n" # undo the set paste done at the begining
        vim_script += "set foldmethod=manual\n\n"
        vim_script += f"execute \"normal! zE\"\n" # remove all folds
        for note_path in map:
            start = map[note_path][0]
            end = map[note_path][1]
            # configure folds per note
            vim_script += f"execute \"normal! :{start},{end}fold\\<cr>\"\n"

        vim_script += f"execute \"normal! zR\"\n" # open folds
        vim_script += f"execute \"normal! gg\"\n" # move cursor to begining

        vim_script_path = "/tmp/knowit.vim"
        open(vim_script_path, "w+").write("".join(vim_script))

        rc = vim(file_path, ["set paste",
                             f"normal i{''.join(lines)}",
                             f":source {vim_script_path}"])

        remove(vim_script_path)

    def browse(self):
        """view to browse the notes using tags"""
        selected = self.args.tags
        all_tags = self.get_tags()

        tag_fzf(self.get_tags(), selected=selected)

    def select(self):
        """
        view select specific note
        - for external usages like linking and embedding notes.
        """
        selected = self.args.tags
        all_tags = self.get_tags()

        note_fzf(self.get_tags(), selected=selected)

    def grep(self):
        """view to search the notes using grep"""

        locations = []
        tags = self.args.tags
        fzf_selected = ""
        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        # in case we in fzf context, initialize accordingly
        if "FZF_QUERY" in environ:
            assert len(tags) == 1
            fzf_selected = self.fzf_selected_parse(tags[0])
            tags = []

        if fzf_label:
            tags = ''.join(fzf_label.split()) # remove all spaces
            tags = tags.strip().split("#")
            tags = [x for x in tags if x] # remove empty strings

        if fzf_query:
            tags.extend(fzf_selected)

        if not tags: locations.append("~/notes") # search all
        else:
            for note in self.notes:
                if not set(tags).issubset(set(note.tags)): continue
                locations.append(note.path)

        result = rg_fzf(locations)
        if not result: return

        file_path = result.split(":")[0]
        file_line = result.split(":")[1]
        vim(file_path, [file_line])

    def tag(self):
        """view to select tags for newly created note"""
        selected = self.args.tags
        on_enter = "echo $FZF_BORDER_LABEL"
        tag_fzf(self.get_tags(), selected=selected, on_enter=on_enter)

    def sync(self):
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

    def fzf_selected_parse(self, selected):
        selected = re.sub(r"\[.*$", "", selected) # remove the count ]
        selected = ''.join(selected.split()) # remove all spaces
        selected = selected.strip().split("#")
        selected = [x for x in selected if x] # remove empty strings
        return selected

    def tag_fzf_reload(self):
        selected = self.args.tags
        assert len(selected) == 1
        selected = self.fzf_selected_parse(selected[0])
        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        tags = []
        if fzf_label:
            tags = ''.join(fzf_label.split()) # remove all spaces
            tags = tags.strip().split("#")
            tags = [x for x in tags if x] # remove empty strings

        # toggle
        if len(selected) == 1:
            if selected[0] in tags:
                tags.remove(selected[0])
            elif selected != "":
                tags.append(selected[0])
        else:
            tags.extend(selected)
        tags = list(set(tags))

        relevant = tags.copy()
        tags_map = {}
        for note in self.notes:
            if not set(tags).issubset(set(note.tags)): continue
            relevant.extend(note.tags)
            relevant = list(set(relevant)) # remove dups
            for tag in note.tags:
                if tag not in tags_map: tags_map[tag] = 0
                tags_map[tag] += 1
        relevant = list(set(relevant))

        for tag, count in reversed(sorted(tags_map.items(), key=lambda x: x[1])):
            print(f"#{tag} [{count}]", flush=True)

        fzf_label = " ".join([f"#{tag}" for tag in tags])

        # we need to re-select the tags for fzf to continue from where we stopped
        post("http://localhost:6266/", data=f"change-border-label({fzf_label})")

    def tag_fzf_preview(self):
        selected = self.args.tags
        assert len(selected) == 1
        selected = self.fzf_selected_parse(selected[0])

        fzf_query = environ.get('FZF_QUERY', "")
        fzf_label = environ.get('FZF_BORDER_LABEL', "")

        tags = []
        if fzf_label:
            tags = ''.join(fzf_label.split()) # remove all spaces
            tags = tags.strip().split("#")
            tags = [x for x in tags if x] # remove empty strings

        if not fzf_query or selected:
            tags.extend(selected)

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

        for note in relevant_notes:
            if prev_existed: content += "\n---\n\n"

            # content += ''.join(note.content)
            content += str(note)
            prev_existed = True

        content = bat(content) if self.args.color else content.encode()
        stdout.buffer.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a',
                        '--action',
                        choices=[
                                    "create",
                                    "browse",
                                    "view",
                                    "tag",
                                    "grep",
                                    "sync",
                                    "tag_fzf_reload",
                                    "tag_fzf_preview",
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
        knowit.create()
    if args.action == "browse":
        knowit.browse()
    if args.action == "view":
        knowit.view()
    if args.action == "grep":
        knowit.grep()
    if args.action == "sync":
        knowit.sync()
    if args.action == "tag":
        knowit.tag()
    if args.action == "tag_fzf_preview":
        knowit.tag_fzf_preview()
    if args.action == "tag_fzf_reload":
        knowit.tag_fzf_reload()


if __name__=="__main__":
    try:
        main()
    except:
        log(traceback.format_exc())
