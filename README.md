# 🚀 Restaurant Analytics Platform

## 📊 Overview

An advanced analytics platform for restaurants, built as a portfolio project to showcase full-stack engineering skills. The platform offers:

- **Intelligent Insights**: Predictive analysis and AI-based recommendations
- **Real-Time Performance**: Continuous monitoring and optimization
- **Intuitive Interface**: Modern design and smooth user experience
- **Data-Driven Decisions**: Strategic support backed by data

Built with modern technologies and a scalable architecture, this platform transforms raw data into strategic decisions for restaurant management.

The solution consists of a Frontend (React), a Backend (FastAPI API), and a Database (PostgreSQL), all orchestrated with Docker.

## 🌟 Key Features

### 📈 Analytics Dashboard
- **Real-Time KPIs**
  - Total Revenue
  - Average Ticket
  - Total Sales
  - Automatic refresh
- **Interactive Charts**
  - Dynamic visualization
  - Advanced filters
  - Data export

### 🛍️ Product Management
- **Detailed Analysis**
  - Individual performance
  - Sales history
  - Channel behavior
  - Temporal trends
- **Automated Insights**
  - Pricing recommendations
  - Cross-sell opportunities
  - Performance alerts

### 📊 Smart Reports
- **Flexible Analytics**
  - Customizable metrics
  - Configurable dimensions
  - Advanced filters
  - Custom time periods
- **Dimension Analysis**
  - Products: Performance and trends
  - Channels: Efficiency and conversion
  - Temporal: Patterns and seasonality
  - Geographic: Distribution and opportunities
- **AI System**
  - Contextual analysis
  - Automatic insights
  - Actionable recommendations
  - Data-based forecasts

### 🤖 AI Insights
- **Predictive Analysis**
  - Demand forecasting
  - Market trends
  - Seasonal patterns
  - Consumer behavior
- **Menu Optimization**
  - Ideal composition
  - Dynamic pricing
  - Product mix
  - Optimized margins
- **Strategic Recommendations**
  - Personalized promotions
  - Profitable combinations
  - Ideal timing
  - Smart segmentation

### 🎨 Design and Visual Identity
- **Modern Interface**
  - Responsive design
  - Intuitive layout
  - Smooth navigation
  - Optimized experience
- **Consistent Branding**
  - Brand colors
  - Visual elements
  - Harmonious typography
  - Unique identity
- **Enhanced Usability**
  - Optimized flows
  - Visual feedback
  - Natural interactions
  - Agile performance

## 🚀 Installation Guide

### Prerequisites
- Docker Engine 20.10+
- Docker Compose v2.0+
- 4GB RAM minimum recommended
- 10GB disk space

### Quick Setup

1. **Data Preparation**
```bash
# Generates a sample dataset with 500k+ records
docker compose run --rm data-generator
```

2. **Platform Initialization**
```bash
# Builds and starts all services
docker compose up -d --build
```

3. **Access the Platform**

After initialization, open:
- **Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Components
- 🖥️ Frontend: React + Material-UI
- 🔧 Backend: FastAPI + PostgreSQL
- 📊 Analytics: Materialized Views
- 🐳 Deploy: Docker + Compose

## 🛠️ Development and Testing

### Tech Stack
- **Frontend**: React 18, Material-UI
- **Backend**: FastAPI, SQLAlchemy
- **Database**: PostgreSQL 14
- **Tests**: Pytest, React Testing Library
- **CI/CD**: Docker, GitHub Actions

### Running Tests

1. **Automated Tests**
```bash
# Runs the full test suite
docker compose run --rm test
```

2. **Test Coverage**
- ✅ API Endpoints
- ✅ Business Logic
- ✅ Integrations
- ✅ Performance

### Code Quality
- 📝 TypeScript for type safety
- 🔍 ESLint + Prettier
- 🧪 Unit and E2E tests
- 🔄 Automated CI/CD

### Security and Stability
- 🔒 Input validation
- 🛡️ Rate limiting
- 📊 Logging and monitoring
- 🔄 Automatic data backup

## 🏛️ Architecture and Performance

### Overview
The platform architecture was designed with a focus on performance, scalability, and user experience. A modern approach that prioritizes query efficiency and interface responsiveness.

### Performance Optimization
- **Challenge**: Complex queries on a database with 500k+ records
- **Goal**: Response time < 500ms for all operations
- **Initial Benchmark**: 1,831ms for complex queries with multiple JOINs

### Implemented Solution
- **Materialized Views**:
  - Abstraction layer for pre-aggregated data
  - Automatic optimization of frequent queries
  - Strategic indexes for performance

- **Layered Architecture**:
  - Optimized React frontend
  - FastAPI with intelligent caching
  - PostgreSQL with materialized views
  - Automatic updates via REFRESH

### Results
- **Performance**: Response time reduced to 122ms
- **Improvement**: 93% optimization in query speed
- **Scale**: Efficient support for large data volumes
- **UX**: Responsive interface with near real-time data

---

## 📝 Release Notes

### v1.0.0
- ✨ Initial release
- 🎯 Complete dashboard
- 🤖 AI system
- 📊 Advanced reports

### Upcoming Features
- [ ] Advanced report export
- [ ] External system integrations
- [ ] Mobile companion app
- [ ] Advanced predictive analytics

### Implementation Notes
- 🔧 Data generator optimization
- 🔄 Circular dependency fixes
- ⚡ Query performance improvements
- 📈 Enhanced scalability