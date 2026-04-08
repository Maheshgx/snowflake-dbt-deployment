-- Setup Secure Views
-- Hide sensitive data from analysts

CREATE OR REPLACE SECURE VIEW {db_name}.{raw_schema}.VW_SECURE_ORDERS AS
SELECT 
    PAYLOAD:order_id::VARCHAR AS ORDER_ID,
    PAYLOAD:customer_id::VARCHAR AS CUSTOMER_ID,
    '*** MASKED ***' AS PAYMENT_INFO,
    LOADED_AT
FROM {db_name}.{raw_schema}.RAW_ORDERS;
