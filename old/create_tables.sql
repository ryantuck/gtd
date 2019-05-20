drop table task;
drop table project;

create table task (

    id              integer primary key autoincrement,
    title           text,
    notes           text,
    done            boolean,
    project_id      integer
);

create table project (

    id              integer primary key autoincrement,
    title           text
);

