# 🍔 The Problem: Analytics for Restaurants

## Context

This project was built to solve a critical problem that affects thousands of restaurants.

## The Persona

**Maria**, owner of 3 restaurants in São Paulo:
- Sells through 5 channels (counter, iFood, Rappi, WhatsApp, own app)
- Has 200+ products on the menu
- Receives ~1,500 orders/week
- Needs to make daily decisions about inventory, prices, and promotions

### Current Pain Points

**Today, Maria can't answer**:
- "Which product sells the most on Thursday nights on iFood?"
- "My average ticket is dropping. Is it by channel or by store?"
- "Which products have the lowest margin and should I rethink their price?"
- "My delivery time has worsened. On which days/hours?"
- "Which customers bought 3+ times but haven't returned in 30 days?"

**She has the data, but can't explore it.**

Fixed dashboards only show pre-defined views. Power BI is too complex and generic. She doesn't have a data team.

## The Real Challenge

Restaurant owners need **customizable and flexible analytics**:
- Simple enough to use without technical training
- Powerful enough to answer complex questions
- Domain-specific (restaurant metrics, not generic ones)

## Available Data

Maria has access to:

### Sales (core)
- Total value, items, discounts, fees
- Time, date, channel, store
- Status (completed, cancelled)
- Times (preparation, delivery)

### Products
- Name, category, price
- Sold in each order
- With options/add-ons

### Customers
- Name, contact, history
- Purchase frequency
- Average ticket

### Operational
- Channels and their commissions
- Store performance
- Payment methods

## What "Good Solution" Means

A good solution allows Maria to:

1. **Explore data freely**
   - Without depending on developers
   - Creating custom visualizations
   - Filtering by any dimension

2. **Get actionable insights**
   - Not just numbers, but meaning
   - Temporal comparisons
   - Anomaly identification

3. **Share with the team**
   - Store manager sees their performance
   - Marketing team sees popular products
   - Business partner sees financial overview

## Technical Constraints

The PostgreSQL database is provided (500k sales).

Everything else is an **architectural decision**:
- Technology stack
- Architecture (monolith, microservices, serverless)
- Frontend framework
- Cache strategy
- Deployment

## Non-Requirements

Not needed:
- Full authentication system (basic mock is fine)
- External system integrations
- Multi-tenancy support
- Scaling to millions of users

Focus on solving the core problem: **customizable and flexible analytics**.

## Questions to Guide the Design

1. How would a non-technical user create a dashboard?
2. How to ensure fast queries even with millions of records?
3. What is the trade-off between flexibility and simplicity?
4. How to make insights visible, not just data?
5. What differentiates restaurant analytics from generic analytics?

## Inspirations

Not to copy, but to inspire:
- **Metabase**: Query builder simplicity
- **Looker**: Business modeling
- **Amplitude**: Analytics UX
- **Grafana**: Visualization flexibility
- **Sheets/Excel (Pivot Tables)**: Visualization flexibility/adaptability

## Success Criteria

Maria should be able to, in **< 5 minutes**:
1. See a revenue overview for the month
2. Identify the top 10 best-selling products in delivery
3. Compare performance of two stores
4. Export a report to present to a business partner

If the solution enables this intuitively, it is on the right track.

---

**This is a real problem that affects thousands of restaurants.**

