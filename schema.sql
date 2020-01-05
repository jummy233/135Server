pragma foreign_keys=on;
create table if not exists user(
    user_id integer primary key autoincrement not null,
    user_name nvarchar(40) not null unique,  -- @conflict.
    last_seen datetime,
    passwd_hash varchar(40),
    permission integer
);

create table if not exists outdoor_spot(
    outdoor_spot_id integer primary key not null,
    outdoor_spot_name nvarchar(40)
);

create table if not exists outdoor_record(
    outdoor_spot_id integer not null,
    outdoor_record_time datetime primary key not null unique,
    outdoor_temperature float,
    outdoor_humidity float,
    wind_direction float,
    wind_speed float,
    wind_chill float,
    solar_radiation float,

    foreign key(outdoor_spot_id) references outdoor_spot(outdoor_spot_id)
    on delete cascade
);

create table if not exists location(
    location_id integer primary key autoincrement not null,
    climate_area_id integer not null,
    province nvarchar(20),
    city nvarchar(20),
    foreign key(climate_area_id) references climate_area(climate_area_id)
    on update cascade on delete set null
);

create table if not exists project(
    project_id integer primary key autoincrement not null,
    outdoor_spot_id integer,
    location_id integer,
    construction_company_id integer,
    tech_support_company_id integer,
    project_company_id integer,
    project_name nvarchar(40),
    floor integer,
    latitude float,
    longitude float,
    district nvarchar(20),
    area float,
    demo_area float,
    building_type nvarchar(40),
    building_height float,
    started_time datetime,
    finished_time datetime,
    record_started_from datetime,
    description nvarchar(800),

    foreign key(location_id) references location(location_id)
    on update cascade on delete cascade,

    foreign key(outdoor_spot_id) references outdoor_spot(outdoor_spot_id)
    on update cascade on delete cascade,

    foreign key(construction_company_id) references company(company_id)
    on update cascade on delete cascade

    foreign key(tech_support_company_id) references company(company_id)
    on update cascade on delete cascade

    foreign key(project_company_id) references company(company_id)
    on update cascade on delete cascade

);

create table if not exists climate_area(
    climate_area_id integer primary key autoincrement not null,
    area_name nvarchar(20)
);

create table if not exists company(
    company_id integer primary key autoincrement not null,
    company_name nvarchar(40)
);

create table if not exists project_detail(
    project_id integer primary key autoincrement not null,
    image blob,
    image_description nvarchar(40),
    foreign key(project_id) references project(project_id)
);

create table if not exists spot(
    spot_id integer primary key autoincrement not null,
    project_id integer not null,
    spot_name nvarchar(20),
    spot_type nvarchar(20),
    image blob,
    foreign key(project_id) references project(project_id)
    on delete cascade
);

create table if not exists device(
    device_id integer primary key autoincrement not null,
    device_name nvarchar(20),
    device_type nvarchar(20),
    spot_id integer not null,
    create_time datetime,
    modify_time datetime,
    foreign key(spot_id) references spot(spot_id)
    on update cascade on delete cascade
);

create table if not exists spot_record(
    spot_record_time datetime primary key not null,
    device_id integer not null,
    temperature float,
    humidity float,
    window_opened boolean,
    ac_power float,
    pm25 integer,
    co2 integer,
    foreign key(device_id) references device(device_id)
    on update cascade on delete cascade
);


