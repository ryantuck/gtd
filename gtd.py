#!/usr/bin/env python3.7
import collections
import datetime
import os
import subprocess

import click

TODAY = datetime.datetime.utcnow().date()

TODOTXT_DIR = os.path.expanduser('~/Dropbox/Apps/Todotxt+/')
TMP_INBOX_PATH = '/tmp/inbox-tmp'

TXT_FILES = ["done", "inbox", "log", "recurring", "tickler", "todo", "tracking"]

CADENCES = ['daily', 'weekly', 'monthly']
ORDERS = {'t': ['5m', '15m', '30m', '1h', '3h', '5d']}

# TODO: use attrs or dataclasses
class Task:
    def __init__(self, line):
        self.line = line

        words = line.split()

        self.is_complete = words[0] == 'x'
        self.completion_date = _get_date(words[1]) if self.is_complete else None

        self.contexts = [w for w in words if w.startswith('@')]
        self.projects = [w for w in words if w.startswith('+')]

        kv_pairs = dict(w.split(':') for w in words if ':' in w)

        self.due_date = _get_date(kv_pairs.get('due', ''))
        self.time_estimate = kv_pairs.get('t')

        # TODO limit these to remove the already-parsed stuff
        self.kv_pairs = kv_pairs

        title_words = [
            w
            for idx, w in enumerate(words)
            if not w.startswith('@')
            and not w.startswith('+')
            and not ':' in w
            and not (self.is_complete and idx == 0)
            and not (self.is_complete and self.completion_date and idx == 1)
        ]
        self.title = ' '.join(title_words)
        self.priority = None
        if self.line.startswith('('):
            self.priority = self.line[1]


def _txt_path(txt_file):
    if txt_file in TXT_FILES:
        return os.path.join(TODOTXT_DIR, f'{txt_file}.txt')
    raise Exception(f'{txt_file} not in {TXT_FILES}')


def _get_date(date_str):
    try:
        return datetime.datetime.fromisoformat(date_str).date()
    except ValueError:
        return None


def _read_todos():
    with open(_txt_path('todo')) as f:
        return [Task(l.strip()) for l in f.readlines() if l != '\n']


def _date_thought(thought):
    return f'{TODAY.isoformat()} {thought}'


def _append(filepath, thoughts):
    with open(filepath, 'a') as f:
        f.writelines([f'{thought}\n' for thought in thoughts])
        f.write('\n')


def vim_to_inbox():
    # edit blank vim canvas, wait to finish
    subprocess.call(f'vim {TMP_INBOX_PATH}', shell=True)

    # read the tmp file
    with open(TMP_INBOX_PATH) as f:
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        body = now + '\n' + f.read()

    # append contents of tmp file to inbox
    with open(_txt_path('inbox'), 'a') as f:
        f.write('\n')
        f.write(body)
        f.write('\n')

    # clear the tmp file
    with open(TMP_INBOX_PATH, 'w') as f:
        pass


# ---------------------------------------------------------------
# File operations
# ---------------------------------------------------------------


@click.command('vim')
@click.argument('txt_file')
def edit_file(txt_file):
    filepath = _txt_path(txt_file)
    subprocess.call(f'vim {filepath}', shell=True)


@click.command('cat')
@click.argument('txt_file')  # TODO add accepted values from enum
def display_file(txt_file):
    cat(txt_file)


# ---------------------------------------------------------------
# Reading
# ---------------------------------------------------------------


@click.command('ls')
@click.option('--group-by', '-g', default='t', help='Value to group on')
@click.option('--where', '-w', default=None, help='List of values to filter on')
def ls(group_by, where):

    where = [] if where is None else where.split(',')
    included = [w for w in where if not w.startswith('~')]
    excluded = [w.lstrip('~') for w in where if w.startswith('~')]

    all_vals = set(
        v for task in _read_todos() for k, v in task.kv_pairs.items() if k == group_by
    )
    vals = sorted(all_vals)
    if group_by in ORDERS:
        vals = [v for v in ORDERS[group_by] if v in all_vals]
    for val in vals:
        print(f'{group_by}:{val}')
        for task in sorted(_read_todos(), key=lambda x: x.title):
            if task.is_complete:
                continue
            # TODO show anything without key as well
            if task.kv_pairs.get(group_by) == val:
                if included != [] and not any(w in task.title for w in included):
                    continue
                if excluded != [] and any(w in task.title for w in excluded):
                    continue
                line = ' '.join(
                    x for x in task.title.split() if not x.startswith(f'{group_by}:')
                )
                print(f'    {line}')


@click.command('contexts')
def contexts():
    counter = collections.Counter(c for task in _read_todos() for c in task.contexts)
    for k, v in counter.most_common():
        print(f'{v} {k}')


@click.command('projects')
def projects():
    counter = collections.Counter(c for task in _read_todos() for c in task.projects)
    for k, v in counter.most_common():
        print(f'{v} {k}')


@click.command('missing-keys')
@click.argument('keys', default='t')
def missing_key(keys):
    keys = keys.split(',')
    for task in _read_todos():
        if all(key in task.kv_pairs for key in keys):
            continue
        print(task.line)


def display_relevant_tickler_items():
    with open(_txt_path('tickler')) as f:
        lines = list(f.readlines())
        items = [
            line.strip()
            for line in lines
            if datetime.datetime.fromisoformat(line.split(' ')[0]).date() <= TODAY
        ]
    if items == []:
        return
    print(f'TICKLER ({len(items)})')
    print('-------')
    for item in items:
        print(item)


def display_overview_todos():
    overview_todos = [
        todo.line
        for todo in _read_todos()
        if todo.priority is not None or (todo.due_date and todo.due_date >= TODAY)
    ]
    print(f'PRIORITY TODOS ({len(overview_todos)})')
    print('-' * len('PRIORITY TODOS'))
    print('\n'.join(overview_todos))


def cat(txt_file):
    with open(_txt_path(txt_file), 'r') as f:
        body = f.read()
    lines = body.split('\n')
    print(f'{txt_file.upper()} ({len(lines)})')
    print('-' * len(txt_file))
    print(body)


@click.command('overview')
def overview():
    display_overview_todos()
    print('\n')
    cat('tracking')
    print('\n')
    display_relevant_tickler_items()


# ---------------------------------------------------------------
# Writing
# ---------------------------------------------------------------


@click.command('inbox')
@click.argument('thought', default='')
def add_to_inbox(thought):
    # if no args are passed, default to vim interface
    if thought == '':
        vim_to_inbox()
        return
    _append(_txt_path('inbox'), [_date_thought(thought)])


@click.command('log')
@click.argument('thought')
def add_to_log(thought):
    _append(_txt_path('log'), [_date_thought(thought)])


@click.command('track')
@click.argument('thought')
def add_to_tracking(thought):
    _append(_txt_path('tracking'), [_date_thought(thought)])


@click.command('add-recurring')
@click.argument('cadence')
def add_recurring_to_todo(cadence):
    if cadence not in CADENCES:
        raise Exception(f'{cadence} not in {CADENCES}')
    with open(_txt_path('recurring'), 'r') as f:
        body = f.read()
    lines = [line for line in body.split('\n') if f'@{cadence}' in line]
    _append(_txt_path('todo'), lines)


# ---------------------------------------------------------------
# CLI
# ---------------------------------------------------------------


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
cli.add_command(edit_file)
cli.add_command(add_recurring_to_todo)

if __name__ == '__main__':
    cli()
