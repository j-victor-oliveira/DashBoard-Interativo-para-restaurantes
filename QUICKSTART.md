# ⚡ Quick Start - 5 Minutes

> **Note**: This is a suggested setup. The base script for data generation is at `./generate_data.py`.

## Full Setup

```bash
# 1. Clone
git clone https://github.com/j-victor-oliveira/DashBoard-Interativo-para-restaurantes.git
cd DashBoard-Interativo-para-restaurantes

docker compose down -v 2>/dev/null || true
docker compose build --no-cache data-generator
docker compose up -d postgres
docker compose run --rm data-generator
docker compose --profile tools up -d pgadmin
```

**Wait 5-15 minutes** while 500k sales are generated.

## Verify

```bash
docker compose exec postgres psql -U challenge challenge_db -c 'SELECT COUNT(*) FROM sales;'

# Should show ~500k
```

## Explore

Explore the generated data however you find most efficient. Browse the tables and understand their relationships.

## Data Structure

```
Sale
├── ProductSale (products)
│   └── ItemProductSale (customizations: +bacon, -onion)
├── Payment (payment methods)
└── DeliverySale (delivery)
    └── DeliveryAddress (with lat/long)
```

**Full schema**: [DADOS.md](./DADOS.md)

## Next Steps

1. **Understand the problem**: Read [PROBLEMA.md](./PROBLEMA.md)
2. **Explore the data**: Run queries, look for patterns
3. **Design the solution**: Architecture, stack, UX
4. **Implement**: Solve the problem!

---

**Setup complete! Time to code. 🚀**
