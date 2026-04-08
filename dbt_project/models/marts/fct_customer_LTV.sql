{{ config(
    materialized='table'
) }}

with revenue as (
    select * from {{ ref('fct_revenue') }}
)

select
    customer_id,
    min(order_date) as first_order_date,
    max(order_date) as last_order_date,
    count(distinct order_id) as total_orders,
    sum(total_revenue) as lifetime_value
from revenue
group by customer_id
