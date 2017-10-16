create table task (

    id              integer primary key autoincrement,
    title           text,
    notes           text            default null,
    done            boolean         default false
);

create table project (

    id              integer primary key autoincrement,
    title           text
);

create table project_task (

    project_id          integer,
    task_id             integer,

    primary key (project_id, task_id)
);
