# 📊 Data Structure

## Overview

This document describes the data generation characteristics adopted by the `generate_data.py` script.

Final result: PostgreSQL database with **6 months of operational data** from restaurants, mirroring a real system managing 1,000+ establishments.

## Main Schema

### Sales Hierarchy

```
Sale
├── Store
├── Channel (in-person/delivery)
├── Customer (optional, 70% identified)
│
├── ProductSales[] (1-5 products per sale)
│   ├── Product
│   └── ItemProductSales[] (customizations: "no onion", "+bacon")
│       ├── Item (add-on/extra)
│       ├── OptionGroup (group: "Add-ons", "Remove")
│       └── ItemItemProductSales[] (nested items)
│
├── Payments[] (1-2 payment methods)
│   └── PaymentType
│
└── DeliverySale (if delivery)
    ├── Courier info
    └── DeliveryAddress
```

### Core Tables

```sql
-- Sales (core)
sales (
    id, store_id, channel_id, customer_id, sub_brand_id,
    created_at, customer_name, sale_status_desc,
    total_amount_items, total_discount, total_increase,
    delivery_fee, service_tax_fee, total_amount, value_paid,
    production_seconds, delivery_seconds, people_quantity,
    discount_reason, origin
)

-- Sold products
product_sales (
    id, sale_id, product_id,
    quantity, base_price, total_price, observations
)

-- Product customizations (e.g.: "Burger + Bacon + Extra Cheese")
item_product_sales (
    id, product_sale_id, item_id, option_group_id,
    quantity, additional_price, price, observations
)

-- Nested customizations (e.g.: "Bacon + Creamy Cheddar")
item_item_product_sales (
    id, item_product_sale_id, item_id, option_group_id,
    quantity, additional_price, price
)

-- Delivery data (delivery orders only)
delivery_sales (
    id, sale_id,
    courier_name, courier_phone, courier_type,
    delivery_type, status, delivery_fee, courier_fee
)

delivery_addresses (
    id, sale_id, delivery_sale_id,
    street, number, complement, neighborhood,
    city, state, postal_code, latitude, longitude
)

-- Payments (a sale can have multiple)
payments (
    id, sale_id, payment_type_id, value, is_online
)

-- Catalog
products (id, brand_id, category_id, name)
items (id, brand_id, category_id, name)  -- Add-ons
option_groups (id, brand_id, name)  -- Option groups
categories (id, brand_id, name, type)  -- 'P' product, 'I' item

-- Entities
stores (id, name, city, state, is_active, is_own)
channels (id, name, type)  -- 'P' in-person, 'D' delivery
customers (id, customer_name, email, phone_number, birth_date)
payment_types (id, description)
```

## Data Volume

```
50 stores → 500,000 sales → 1.2M products sold → 800k customizations
         ↓
   10k customers (70% of sales identified)
```

### Distribution

**Sales by channel**:
- In-person: 40% (~200k sales)
- iFood: 30% (~150k)
- Rappi: 15% (~75k)
- Others: 15% (~75k)

**Products**:
- 500 base products
- 200 items/add-ons
- Average 2.4 products per sale
- 60% of sales have customizations

**Customers**:
- 10,000 registered
- 30% of sales are "guest" (no registration)
- Distribution: 70% bought 1-3x, 20% 4-10x, 10% 10+x

## Temporal Patterns

### Intra-day
```
00-06h: 2% of sales
06-11h: 8%
11-15h: 35% ⚡ (lunch)
15-19h: 10%
19-23h: 40% ⚡ (dinner)
23-24h: 5%
```

### Weekly
```
Monday:    -20% vs average
Tuesday:   -10%
Wednesday:  -5%
Thursday:    0% (baseline)
Friday:    +30%
Saturday:  +50% ⚡
Sunday:    +40%
```

### Monthly
- Gradual growth: ~2-3% month over month
- Random variation: ±10%

## Realistic Data

### Typical Values

```
General average ticket: R$ 65
├── In-person: R$ 45-55
├── iFood: R$ 70-85
└── Rappi: R$ 65-80

Operational times:
├── Preparation: 5-40 min (avg 18 min)
└── Delivery: 15-60 min (avg 35 min)

Rates:
├── Cancellation: ~5%
├── With discount: ~20%
└── With customization: ~60%
```

### Injected Anomalies

Intentionally included to test analytics:

1. **Problematic week**: 30% drop in sales (simulates operational issue)
2. **Promotional day**: 3x peak (Black Friday, promotion)
3. **Growing store**: One specific store with 5%/month linear growth
4. **Seasonal product**: Some products sell 80% more in certain months

**The solution should allow identifying these patterns.**

## Data Complexity

### Real Sale Example

```
Sale #12345
├── Store: "Burguer House - Centro SP"
├── Channel: iFood
├── Customer: João Silva (identified)
├── Total: R$ 87.50
│
├── Products:
│   ├── Double X-Bacon (R$ 32.00)
│   │   ├── + Extra Bacon (R$ 5.00)
│   │   ├── + Creamy Cheddar (R$ 4.00)
│   │   └── - Onion (R$ 0.00)
│   │
│   ├── Large French Fries (R$ 18.00)
│   │   └── + Cheddar (R$ 3.00)
│   │
│   └── 2L Soda (R$ 12.00)
│
├── Discount: -R$ 8.50 (loyalty coupon)
├── Delivery fee: +R$ 9.00
├── Total: R$ 87.50
│
├── Payment: PIX (R$ 87.50)
│
├── Times:
│   ├── Preparation: 22 minutes
│   └── Delivery: 38 minutes
│
└── Delivery:
    ├── Courier: Carlos (iFood)
    └── Address: Rua X, 123, Centro
```

This structure enables analyses such as:
- "Which add-on item is most sold?"
- "Products that most receive removals?"
- "Delivery time by region?"
- "Payment mix by channel?"

## Example Queries

```sql
-- Full sales with products and customizations
SELECT 
    s.id, s.created_at, s.total_amount,
    st.name as store, ch.name as channel,
    p.name as product,
    ps.quantity,
    array_agg(i.name) as customizations
FROM sales s
JOIN stores st ON st.id = s.store_id
JOIN channels ch ON ch.id = s.channel_id
JOIN product_sales ps ON ps.sale_id = s.id
JOIN products p ON p.id = ps.product_id
LEFT JOIN item_product_sales ips ON ips.product_sale_id = ps.id
LEFT JOIN items i ON i.id = ips.item_id
WHERE s.sale_status_desc = 'COMPLETED'
  AND DATE(s.created_at) = '2024-01-15'
GROUP BY s.id, st.name, ch.name, p.name, ps.quantity
LIMIT 10;

-- Top items/add-ons most sold
SELECT 
    i.name as item,
    COUNT(*) as times_added,
    SUM(ips.additional_price) as revenue_generated
FROM item_product_sales ips
JOIN items i ON i.id = ips.item_id
JOIN product_sales ps ON ps.id = ips.product_sale_id
JOIN sales s ON s.id = ps.sale_id
WHERE s.sale_status_desc = 'COMPLETED'
GROUP BY i.name
ORDER BY times_added DESC
LIMIT 20;

-- Delivery performance by region
SELECT 
    da.neighborhood,
    da.city,
    COUNT(*) as deliveries,
    AVG(s.delivery_seconds / 60.0) as avg_delivery_minutes,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY s.delivery_seconds / 60.0) as p90_delivery_minutes
FROM sales s
JOIN delivery_addresses da ON da.sale_id = s.id
WHERE s.sale_status_desc = 'COMPLETED'
  AND s.delivery_seconds IS NOT NULL
GROUP BY da.neighborhood, da.city
HAVING COUNT(*) >= 10
ORDER BY avg_delivery_minutes DESC;
```

## Generation Script

Run to populate the database:

```bash
python generate_data.py \
    --months 6 \
    --stores 50 \
    --products 500 \
    --items 200 \
    --customers 10000
```

This generates:
- ~500k sales
- ~1.2M products sold
- ~800k customizations (items)
- ~200k deliveries with address
- ~600k payments

**Estimated time**: 5-15 minutes depending on the machine.

## What This Enables

With this complete structure, the solution can answer:

- Total revenue, average ticket, sales per day
- Store and product rankings
- Performance by channel and time of day
- Cancellation rate and reasons
- Discount analysis
- **Customizations**: Which items are most sold? Which products receive the most changes?
- **Delivery**: Average time by region? Which neighborhoods order the most?
- **Product mix**: Which combinations appear together?
- **Customer journey**: Frequency, retention, lifetime value
- Temporal anomaly detection
- Demand forecasting by product
- Customer segmentation
- Delivery route optimization

---

**The complexity of the data reflects real operations. Use this to create rich analytics.**

