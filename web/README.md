# census-map
A universal map visualiser for all census data:
- Displays any combination of stats
- Stats are shown as percentages against total population, except for averages and medians (i.e they're normalised)
- Map shading shows range of values on the map (not the National range) - highlights min/max areas in view
- Bookmarks for all capital cities
- Note: not necessarily mobile friendly!

### Pre-requisites
- Run census-loader to import the Census data and boundaries into Postgres
- Python 3.x with Psycopg2, Flask and Flask Compress packages installed

### Process
1. Run server.py with your arguments (below)
2. Open your browser at [http://127.0.0.1:8081](http://127.0.0.1:8081)
3. Enjoy!

#### Postgres Arguments
* `--pghost` the host name for the Postgres server. This defaults to the `PGHOST` environment variable if set, otherwise defaults to `localhost`.
* `--pgport` the port number for the Postgres server. This defaults to the `PGPORT` environment variable if set, otherwise `5432`.
* `--pgdb` the database name for Postgres server. This defaults to the `PGDATABASE` environment variable if set, otherwise `psma_201602`.
* `--pguser` the username for accessing the Postgres server. This defaults to the `PGUSER` environment variable if set, otherwise `postgres`.
* `--pgpassword` password for accessing the Postgres server. This defaults to the `PGPASSWORD` environment variable if set, otherwise `password`.

#### Optional Arguments
* `--census-year` year of the ABS Census data to load. Valid values are `2011` and `2016` Defaults to `2016`.
* `--data-schema` schema name to store Census data tables in. Defaults to `census_2016_data`. **You will need to change this argument if you set `--census-year=2011`**
* `--boundary-schema` schema name to store Census boundary tables in. Defaults to `census_2016_bdys`. **You will need to change this argument if you set `--census-year=2011`**
* `--web-schema` schema name to store Census boundary tables in. Defaults to `census_2016_web`. **You will need to change this argument if you set `--census-year=2011`**

### Example Command Line Arguments
`python server.py`

Runs the map for 2016 Census data using the the default database and schema names.

`python server.py --census-year=2011 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --web-schema=census_2011_web`

Runs the map for 2011 Census data.

### URL Parameters

* `stats` comma-delimited list of sequential IDs for the stats to display (e.g. g4,g5,g6). Defaults to total persons (i.e g1,g2,g3 for 2016, b1,b2,b3 for 2011)
* `census` the census year (2011 or 2016). Defaults to 2016
* `z` the start zoom level for the map. Defaults to level 12
* `b` boundary type override (e.g. 'sa1'). Use this to lock the map to show one type of boundary at multiple zoom levels. The default map will change boundary type as you zoom in and out to show the most relevant data

### Usage

1. Get the map server running
2. Lookup the stats you want from the Metadata Excel files in the Census Datapacks ()
3. Add them to the URL for the map. e.g. http://127.0.0.1:8081/?stats=T01,T02,T03

Note: an intuitive, keyword based stat search tool would be good to integrate with the map, but I'd like to get some rest now... (pull requests gratefully accepted)

### Examples

* Age: [http://127.0.0.1:8081/?stats=G247,G248,G249,G250,G251,G252,G253,G254,G255](http://127.0.0.1:8081/?stats=G247,G248,G249,G250,G251,G252,G253,G254,G255)
* Religion: [http://127.0.0.1:8081/?stats=G5456,G5363,G5423,G5426,G5429,G5432](http://127.0.0.1:8081/?stats=G5456,G5363,G5423,G5426,G5429,G5432)
* Median age, income, rent, mortgages: [http://127.0.0.1:8081/?stats=G109,G110,G111,G112,G113,G114,G115,G116](http://127.0.0.1:8081/?stats=G109,G110,G111,G112,G113,G114,G115,G116)

### Data License

Source: [Australian Bureau of Statistics](http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material)
