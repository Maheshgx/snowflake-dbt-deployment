-- Setup Raw Tables
-- Using placeholders for dynamic environment deployment

CREATE TABLE IF NOT EXISTS {db_name}.{raw_schema}.RAW_ORDERS (
    PAYLOAD VARIANT,
    LOADED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS {db_name}.{raw_schema}.RAW_CUSTOMERS (
    PAYLOAD VARIANT,
    LOADED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
