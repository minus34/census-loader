#!/bin/bash

while ! PGPASSWORD=census psql -h db -U census -l >/dev/null; do
  echo "** Waiting for PostgreSQL to start up and be ready for queries. **"
  sleep 5
done

echo "** Launching loader **"
python load-census.py --census-data-path /data/ --census-bdys-path /data/ --pghost db --pgdb census --pguser census --pgpassword census
