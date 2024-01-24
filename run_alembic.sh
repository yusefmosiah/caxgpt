#!/bin/bash

# Check if the migrations directory exists
if [ ! -d "db-migrations/versions" ]; then
  # Run the commands if it doesn't
  alembic revision --autogenerate -m "Add Todos Table"
  alembic upgrade head
fi
