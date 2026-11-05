-- Runs first in docker-entrypoint-initdb.d (before 10_base_schema.sql):
-- the pytest suite uses a separate database on the same server.
CREATE DATABASE payment_shop_test;
