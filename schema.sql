PRAGMA foreign_keys=on;
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_name NVARCHAR(40) NOT NULL UNIQUE,  -- @conflict.
    last_seen TEXT,
    passwd_hash VARCHAR(40),
    permission INTEGER
);

CREATE TABLE IF NOT EXISTS outdoor_spots(
    outdoor_spot_id INTEGER PRIMARY KEY NOT NULL,
    outdoor_spot_name NVARCHAR(40),
);

CREATE TABLE IF NOT EXISTS outdoor_records(
    outdoor_spot_id INTEGER NOT NULL,
    outdoor_record_time TEXT PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    outdoor_tempreture FLOAT,
    outdoor_humidity FLOAT,
    -- sun_radiation
    chilling_temperature FLOAT,
    wind_direction FLOAT,
    wind_speed FLOAT,
    FOREIGN KEY(outdoor_spot_id) REFERENCES outdoor_spots(outdoor_spot_id),
);

CREATE TABLE IF NOT EXISTS locations(
    location_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    climate_area_id INTEGER NOT NULL,
    province NVARCHAR(20),
    city NVARCHAR(20),
    FOREIGN KEY(climate_area_id) REFERENCES climate_areas(climate_area_id)
);

CREATE TABLE IF NOT EXISTS projects(
    project_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    outdoor_spot_id INTEGER,
    location_id INTEGER,
    company_id INTEGER,
    project_name NVARCHAR(40),
    floor INTEGER,
    latitude FLOAT,
    longitude FLOAT,
    district NVARCHAR(20),
    area FLOAT,
    demo_area FLOAT,
    building_type NVARCHAR(40),
    building_height Float,
    finished_time TEXT,
    record_started_from TEXT,
    record_ended_by TEXT,
    description NVARCHAR(800),
    FOREIGN KEY(outdoor_spot_id) REFERENCES outdoor_spots(outdoor_spot_id),
    FOREIGN KEY(location_id) REFERENCES locations(location_id),
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS climate_areas(
    climate_area_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    area_name NVARCHAR(20)
);

CREATE TABLE IF NOT EXISTS companies(
    company_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    construction_company NVARCHAR(40),
    tech_support_company NVARCHAR(40),
    project_company NVARCHAR(40)
);

CREATE TABLE IF NOT EXISTS project_details(
    project_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    image BLOB,
    image_description NVARCHAR(40),
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS spots(
    spot_id INTEGER PRIMARY KEY NOT NULL,
    project_id INTEGER NOT NULL,
    spot_name NVARCHAR(20),
    image BLOB,
    FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS spot_records(
    spot_id INTEGER NOT NULL,
    spot_record_time TEXT PRIMARY KEY NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    energy_consumption FLOAT,
    pm25 INTEGER,
    co2 INTEGER,
    FOREIGN KEY(spot_id) REFERENCES spots(spot_id),
);

CREATE TABLE IF NOT EXISTS devices(
    device_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    spot_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY(device_id) REFERENCES spots(spot_id)
);
