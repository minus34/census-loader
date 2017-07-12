# census-map
A universal map visualiser for all census data.

### Pre-requisites
- Running census-loader to import the data and boundaries into Postgres
- Python 3.x with Psycopg2, Flask and Flask Compress packages installed

### Process
1. Run server.py with the right parameters (below)
2. Open your browser at [http://127.0.0.1:8081](http://127.0.0.1:8081)
3. Enjoy

#### Postgres Parameters
* `--pghost` the host name for the Postgres server. This defaults to the `PGHOST` environment variable if set, otherwise defaults to `localhost`.
* `--pgport` the port number for the Postgres server. This defaults to the `PGPORT` environment variable if set, otherwise `5432`.
* `--pgdb` the database name for Postgres server. This defaults to the `PGDATABASE` environment variable if set, otherwise `psma_201602`.
* `--pguser` the username for accessing the Postgres server. This defaults to the `PGUSER` environment variable if set, otherwise `postgres`.
* `--pgpassword` password for accessing the Postgres server. This defaults to the `PGPASSWORD` environment variable if set, otherwise `password`.

#### Optional Arguments
* `--census-year` Year of the ABS Census data to load. Valid values are `2011` and `2016` Defaults to `2016`.
* `--data-schema` schema name to store Census data tables in. Defaults to `census_2016_data`. **You will need to change this argument if you set `--census-year=2011`**
* `--boundary-schema` schema name to store Census boundary tables in. Defaults to `census_2016_bdys`. **You will need to change this argument if you set `--census-year=2011`**
* `--web-schema` schema name to store Census boundary tables in. Defaults to `census_2016_web`. **You will need to change this argument if you set `--census-year=2011`**
* `--max-processes` specifies the maximum number of parallel processes to use for the data load. Set this to the number of cores on the Postgres server minus 2, but limit to 12 if 16+ cores - there is minimal benefit beyond 12. Defaults to 3.

### Example Command Line Arguments
`python server.py`

Runs the map for 2016 Census data using the the default database and schema names.

`python server.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web`

Runs the map for 2011 Census data.

### Data Licenses

Source: [Australian Bureau of Statistics](http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material)
