The Problem: The Pain of Maria (and the Dev)

The PROBLEM.md describes Maria, who needs flexible analytics, and the FAQ.md establishes a performance requirement of < 500ms per query.

To validate the challenge, the first step was to run the complex queries (like the ones Maria would run) directly against the database populated with 542,773 sales.

The Diagnosis (The Proof):

Queries requiring 3 or 4 JOINs (e.g.: sales, products, channels) had the following performance:

Maria's Query (Top Products on iFood): 1,831 ms

Item Query (Top Add-ons): 1,391 ms

Delivery Query (Average by Neighborhood): 1,156 ms

Conclusion: All queries failed the < 500ms requirement. A dashboard that takes 2 seconds to load is unacceptable.

The Solution: Aggregation Layer (Materialized Views)

The architectural decision was to not query the transactional tables (OLTP) directly. Instead, an aggregation layer (OLAP) was created using PostgreSQL Materialized Views.

The `mv_sales_analytics` view was created, which pre-calculates all complex JOINs and extracts dimensions (such as day_of_week, hour_of_day).

Optimized indexes were created on this view for the most common filters (channel, day, hour).

The Result (Proof of Solution):

The most complex Maria query was repeated, but this time querying `mv_sales_analytics`:

Previous Performance: 1,831 ms

Optimized Performance: 122 ms

Gains:

A 15x performance improvement.

Easily meets the < 500ms requirement.

The Backend (API) is simple and fast, as it only queries this view.

Trade-off: Data is not 100% "real-time" (the view needs a refresh, e.g. every 5 min). For managerial analytics, this is a perfectly acceptable trade-off.