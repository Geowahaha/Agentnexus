-- Run as PostgreSQL superuser, e.g.:
-- psql -U postgres -h localhost -f scripts/init_database.sql

CREATE USER agentnexus WITH PASSWORD 'agentnexus';
CREATE DATABASE agentnexus OWNER agentnexus;
GRANT ALL PRIVILEGES ON DATABASE agentnexus TO agentnexus;