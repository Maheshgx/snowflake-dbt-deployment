{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='append_new_columns'
) }}

SELECT 
    order_id,
    customer_id,
    order_date,
    SUM(item_price * quantity) as total_revenue
FROM {{ ref('stg_orders') }}
{% if is_incremental() %}
    WHERE order_date >= (SELECT MAX(order_date) FROM {{ this }})
{% endif %}
GROUP BY 1, 2, 3
