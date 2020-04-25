import os
import tempfile

import networkx as nx


NOTES_PATH = '/Users/ryan/Dropbox/notes'


def ls():
    return [
        os.path.splitext(f)[0]
        for f in os.listdir(NOTES_PATH)
        if not f.startswith('.') and f.endswith('.md')
    ]


def read(note):
    filepath = os.path.join(NOTES_PATH, f'{note}.md')
    with open(filepath) as f:
        return f.read()


def _is_tag(word):
    # TODO: improve with regex
    return (word.startswith('#') and not set(word) == set('#')) or word.startswith('+')


def get_tags(body):
    return sorted(set(w.replace('+', '#') for w in body.split() if _is_tag(w)))


def edges():
    graph_edges = []
    for note in ls():
        src = f'#{note}'
        tags = get_tags(read(note))
        for tag in tags:
            if src == tag:
                continue
            graph_edges.append((src, tag))
    return sorted(set(graph_edges))


def generate_dot():
    # TODO: do something with this output in-browser!
    g = nx.DiGraph()
    g.add_edges_from(edges())
    g.remove_node('#_index')
    g.remove_node('#archive')
    with tempfile.NamedTemporaryFile() as tmp:
        nx.drawing.nx_agraph.write_dot(g, tmp.name)
        return tmp.read().decode('utf-8')


def _format_tag(tag):
    note = tag.strip('#')
    return f'[{tag}]({note}.md)'


def _maybe_format(word):
    if _is_tag(word):
        return _format_tag(word)
    return word


def flesh_out_note(note):
    body = read(note)
    words = [_maybe_format(w) for w in body.split()]
    return ' '.join(words)
