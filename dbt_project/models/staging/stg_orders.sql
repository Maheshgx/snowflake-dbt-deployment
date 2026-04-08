with source as (
    -- In a real setup, you might use {{ source('raw', 'orders') }}
    select * from {{ source('shopstream_raw', 'raw_orders') }}
),

renamed as (
    select
        id as order_id,
        user_id as customer_id,
        status as order_status,
        created_at as order_date,
        item_price,
        quantity
    from source
)

select * from renamed
