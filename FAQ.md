# ❓ FAQ

## About the Project

### How long did this take to build?

The project was built in approximately one week, with a focus on quality over quantity.

## Technologies

### Can I use this project as a reference?

Yes! Use it as you see fit. Just make sure you understand what is being used.

### Was this built from scratch?

Yes, the dashboard was built from scratch to fully address the user's needs.

### Are frontend and backend both required?

Yes. The solution needs a visual interface for the user to explore data. Data aggregation beyond SQL is also needed.

## Data

### How do I get the data?

Clone the repository and run the script / docker compose to generate the data.

### Can I generate more data?

Yes, use the `generate_data.py` script with different parameters.

### Is the data realistic?

More or less. Based on an attempt to reproduce real patterns from 50+ restaurants. Includes seasonality, anomalies, and real distributions.

## Implementation

### Is drag-and-drop implemented?

Not mandatory. There is a better way to create custom dashboards.

### Is a visual query builder implemented?

Not as a separate feature. Data exploration is done through the dashboard's built-in filters and report builder.

### How many advanced features are included?

The focus was on solving the core problem very well. Extra features are bonuses, not requirements.

### Is authentication required?

No authentication was implemented for this project.

### Are queries fast?

Yes. 500ms for complex queries is the target. 2+ seconds is unacceptable. Performance matters.

## Setup

### Is a video walkthrough available?

Not currently, but the README provides a complete setup guide.

### Do I need to deploy it?

Not required. Running `docker compose up` works perfectly locally.

### What if it doesn't work on the first try?

Follow the instructions in the README: "Clone, docker compose up, access localhost:3000".

## Architecture

### Why this tech stack?

Good engineering was prioritized over any specific technology. The choices were made based on what made sense for the problem.

### Can I use unfamiliar technologies?

Yes, as long as the code is well-documented and the choices make sense.

### Can I use open source library code?

Yes, with proper credits. Do not copy solutions from other developers.

