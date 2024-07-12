# knowit

## Requirements
- [fzf](https://github.com/junegunn/fzf)
- [bat](https://github.com/sharkdp/bat)

## Examples
- `python knowit.py -a select`
    - fzf bindings:
        ```python
        fzf_options = "--bind 'ctrl-z:toggle-preview' "
        fzf_options += "--bind 'ctrl-k:preview-up' "
        fzf_options += "--bind 'ctrl-j:preview-down' "
        fzf_options += "--bind 'ctrl-u:preview-half-page-up' "
        fzf_options += "--bind 'ctrl-d:preview-half-page-down' "
        fzf_options += "--bind 'esc:clear-query' "
        ```
- `python knowit.py -a view -t <tag>...<tag> [--color]`
- `python knowit.py -a create`


