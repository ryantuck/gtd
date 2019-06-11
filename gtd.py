#!/usr/bin/env python3.7
import collections

import click

TODO_PATH = "/Users/ryan.tuck/Dropbox/Apps/Todotxt+/todo.txt"

ORDERS = {
    'do': ['m', 't', 'w', 'r', 'f', 'sa', 'su'],
    't': ['5m', '15m', '30m', '1h', '3h', '5d'],
}


def _read():
    with open(TODO_PATH) as f:
        lines = list(enumerate(f.readlines()))
    return [f'{line.strip()} [{idx+1}]' for idx, line in lines]


def parse_attributes(line):
    pairs = [tuple(x.split(':')) for x in line.split() if ':' in x]
    return {k: v for k, v in pairs}


def parse_contexts(line):
    return [x for x in line.split() if x.startswith('@')]


def parse_projects(line):
    return [x for x in line.split() if x.startswith('+')]


@click.command('contexts')
def contexts():
    counter = collections.Counter(c for line in _read() for c in parse_contexts(line))
    for k, v in counter.most_common():
        print(f'{v} {k}')


@click.command('projects')
def projects():
    counter = collections.Counter(c for line in _read() for c in parse_projects(line))
    for k, v in counter.most_common():
        print(f'{v} {k}')


@click.command('ls')
@click.option('--group-by', '-g', default='t', help='Value to group on')
@click.option('--where', '-w', default=None, help='List of values to filter on')
def ls(group_by, where):

    where = [] if where is None else where.split(',')
    included = [w for w in where if not w.startswith('~')]
    excluded = [w.lstrip('~') for w in where if w.startswith('~')]

    all_vals = set(
        v
        for line in _read()
        for k, v in parse_attributes(line).items()
        if k == group_by
    )
    vals = sorted(all_vals)
    if group_by in ORDERS:
        vals = [v for v in ORDERS[group_by] if v in all_vals]
    for val in vals:
        print(f'{group_by}:{val}')
        for line in sorted(_read()):
            if parse_attributes(line).get(group_by) == val:
                if included != [] and not any(w in line for w in included):
                    continue
                if excluded != [] and any(w in line for w in excluded):
                    continue
                line = ' '.join(
                    x for x in line.split() if not x.startswith(f'{group_by}:')
                )
                print(f'    {line}')


@click.command('missing-keys')
@click.argument('keys')
def missing_key(keys):
    keys = keys.split(',')
    for line in _read():
        attributes = parse_attributes(line)
        if all(key in attributes for key in keys):
            continue
        print(line)


@click.group()
def cli():
    pass


cli.add_command(ls)
cli.add_command(contexts)
cli.add_command(projects)
cli.add_command(missing_key)

if __name__ == '__main__':
    cli()
