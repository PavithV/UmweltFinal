CREATE TABLE IF NOT EXISTS measurements (
    time        TIMESTAMPTZ       NOT NULL,
    sensor_id   TEXT              NOT NULL,
    sensor_name TEXT,
    unit TEXT,
    value       DOUBLE PRECISION  NOT NULL,
    PRIMARY KEY (time, sensor_id)
);

-- Create hypertable
SELECT create_hypertable('measurements', 'time', if_not_exists => TRUE);
SELECT add_retention_policy('measurements', INTERVAL '7 days');