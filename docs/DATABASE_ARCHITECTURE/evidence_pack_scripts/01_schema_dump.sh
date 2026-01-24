#!/bin/bash
pg_dump --schema-only --no-owner --no-privileges "$DB_NAME" > schema_dump.sql
