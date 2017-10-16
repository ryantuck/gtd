create table task (

    id              integer primary key autoincrement,
    title           text,
    notes           text            default null,
    done            boolean         default false,
    project_id      integer         default null
);

create table project (

    id              integer primary key autoincrement,
    title           text
);

