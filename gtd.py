#!/usr/bin/env python3.7
import collections
import datetime
import os

import click

EXPECTED_KEYS = ['t']

TODAY = datetime.datetime.utcnow().date().isoformat()

TODOTXT_DIR = "/Users/ryan/Dropbox/Apps/Todotxt+/"
INBOX_PATH = os.path.join(TODOTXT_DIR, "inbox.txt")
LOG_PATH = os.path.join(TODOTXT_DIR, "log.txt")
TODO_PATH = os.path.join(TODOTXT_DIR, "todo.txt")
DONE_PATH = os.path.join(TODOTXT_DIR, "done.txt")
TRACKING_PATH = os.path.join(TODOTXT_DIR, "tracking.txt")

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
@click.argument('keys', default='t')
def missing_key(keys):
    keys = keys.split(',')
    for line in _read():
        attributes = parse_attributes(line)
        if all(key in attributes for key in keys):
            continue
        print(line)

def _date_thought(thought):
    return f'{TODAY} {thought}'

def _append(filepath, thought):
    with open(filepath, 'a') as f:
        f.writelines([_date_thought(thought)])
        f.write('\n')


@click.command('inbox')
@click.argument('thought')
def add_to_inbox(thought):
    _append(INBOX_PATH, thought)

@click.command('log')
@click.argument('thought')
def add_to_log(thought):
    _append(LOG_PATH, thought)

@click.command('track')
@click.argument('thought')
def add_to_tracking(thought):
    _append(TRACKING_PATH, thought)



def cat(txt_file):
    print(txt_file.upper())
    print('-' * len(txt_file))
    with open(os.path.join(TODOTXT_DIR, f'{txt_file}.txt'), 'r') as f:
        return f.read()


@click.command('overview')
def overview():
    print(cat('inbox'))
    print('\n')
    print(cat('tracking'))


@click.command('cat')
@click.argument('txt_file')  # add accepted values
def display_file(txt_file):
    print(cat(txt_file))

@click.group()
def cli():
    pass


cli.add_command(add_to_inbox)
cli.add_command(add_to_log)
cli.add_command(add_to_tracking)
cli.add_command(contexts)
cli.add_command(display_file)
cli.add_command(ls)
cli.add_command(missing_key)
cli.add_command(overview)
cli.add_command(projects)

if __name__ == '__main__':
    cli()
