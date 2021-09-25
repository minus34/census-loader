# census-loader
A quick way to get started with Australian Bureau of Statistics (ABS) Census 2011 or 2016 data.

**census-loader is 2 things:**
1. A quick way to load the entire census into Postgres
2. A [map server](https://github.com/minus34/census-loader/tree/master/web) for quickly visualising census data and trends

**DEMOS** (CURRENTLY OFFLINE)

* Age: [https://census.minus34.com?stats=G247,G248,G249,G250,G251,G252,G253,G254,G255](https://census.minus34.com?stats=G247,G248,G249,G250,G251,G252,G253,G254,G255)
* Religion: [https://census.minus34.com?stats=G5456,G5363,G5423,G5426,G5429,G5432](https://census.minus34.com?stats=G5456,G5363,G5423,G5426,G5429,G5432)
* Median age, income, rent, mortgages: [https://census.minus34.com?stats=G109,G110,G111,G112,G113,G114,G115,G116](https://census.minus34.com?stats=G109,G110,G111,G112,G113,G114,G115,G116)
* Country of birth: [https://census.minus34.com?stats=G2320,G2380,G2410,G2450,G2470,G2520,G2620,G2660,G2780](https://census.minus34.com?stats=G2320,G2380,G2410,G2450,G2470,G2520,G2620,G2660,G2780)


![melbourne_rent.png](https://github.com/minus34/census-loader/blob/master/sample-images/melbourne_rent.png)

### There are 3 options for loading the data
1. [Run](https://github.com/minus34/census-loader#option-1---run-loadcensuspy) the load-census Python script and build the database schemas in a single step
2. [Build](https://github.com/minus34/census-loader#option-2---build-the-database-in-a-docker-environment) the database in a docker environment.
3. [Download](https://github.com/minus34/census-loader#option-3---load-pg_dump-files) the Postgres dump files and restore them in your database. __Note: Census 2016 data and ASGS boundaries only__

## Option 1 - Run load-census.py
Running the Python script takes 15-30 minutes on a Postgres server configured for performance.

Benchmarks are:
- 3 year old, 32 core Windows server with SSDs = 15 mins
- MacBook Pro = 25 mins

### Performance
To get a good load time you'll need to configure your Postgres server for performance. There's a good guide [here](https://revenant.ca/www/postgis/workshop/tuning.html), noting it's a few years old and some of the memory parameters can be beefed up if you have the RAM.

### Pre-requisites
- Postgres 9.6+ with PostGIS 2.3+ (tested on 9.6 on macOS Sierra and Windows 10)
- Add the Postgres bin directory to your system PATH
- Python 3.x with Psycopg2, xlrd & Pandas packages installed

### Process
1. Download [ABS Census DataPacks](https://datapacks.censusdata.abs.gov.au/datapacks/)
2. Download [ABS 2016 ASGS boundaries](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.001) or [ABS 2011 ASGS boundaries](https://www.abs.gov.au/websitedbs/censushome.nsf/home/datapacks) (requires a free login) **IMPORTANT - download the ESRI Shapefile versions**
3. (optional) Download the 2016 [Indigenous](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.002) and [Non-ABS](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.003) boundaries as well
4. Unzip the Census CSV files to a directory on your Postgres server
5. Alter security on the directory to grant Postgres read access
6. Unzip the ASGS boundaries to a local directory
7. Create the target database (if required)
8. Check the optional and required arguments by running load-census.py with the `-h` argument (see command line examples below)
9. Run the script, come back in 10-15 minutes and enjoy!

### Command Line Options
The behaviour of census-loader can be controlled by specifying various command line options to the script. Supported arguments are:

#### Required Arguments
* `--census-data-path` specifies the path to the extracted Census metadata and data tables (eg *.xlsx and *.csv files). __This directory must be accessible by the Postgres server__, and the corresponding local path for the server to this directory may need to be set via the `local-server-dir` argument
* `--census-bdys-path` specifies the path to the extracted ASGS boundary files. Unlike `census-data-path`, this path does not necessarily have to be accessible to the remote Postgres server.

#### Postgres Parameters
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
* `--max-processes` specifies the maximum number of parallel processes to use for the data load. Set this to the number of cores on the Postgres server minus 2, but limit to 12 if 16+ cores - there is minimal benefit beyond 12. Defaults to 3.

### Example Command Line Arguments
`python load-census.py --census-data-path="C:\temp\census_2016_data" --census-bdys-path="C:\temp\census_2016_boundaries"`

Loads the 2016 Census data using a maximum of 3 parallel processes into the default schemas. Census data archives have been extracted to the folder `C:\temp\census_2016_data`, and ASGS boundaries have been extracted to the `C:\temp\census_2016_boundaries` folder.

`python load-census.py --census-year=2011 --max-processes=6 --data-schema=census_2011_data --boundary-schema=census_2011_bdys --census-data-path="C:\temp\census_2011_data" --census-bdys-path="C:\temp\census_2011_boundaries"`

Loads the 2011 Census data using a maximum of 6 parallel processes into renamed schemas. Census data archives have been extracted to the folder `C:\temp\census_2011_data`, and ASGS boundaries have been extracted to the `C:\temp\census_2011_boundaries` folder.

### Attribution
When using the resulting data from this process - you will need to adhere to the ABS data attribution requirements for the [Census and ASGS data](https://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material), as per the Creative Commons (Attribution) license.

### WARNING:
- The scripts will DROP ALL TABLES and recreate them using CASCADE; meaning you'll LOSE YOUR VIEWS if you have created any! If you want to keep the existing data - you'll need to change the schema names in the script or use a different database

### IMPORTANT:
- Whilst you can choose which 3 schemas to load the data into, I haven't QA'd the permutations. Stick with the defaults if you have limited Postgres experience 

## Option 2 - Build the database in a docker environment

Create a Docker container with Census data and ASGS boundaries ready to go, so they can be deployed anywhere.

### Process
1. Download [ABS Census DataPacks](https://datapacks.censusdata.abs.gov.au/datapacks/)
2. Download [ABS 2016 ASGS boundaries](https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/1270.0.55.001July%202016) or [ABS 2011 ASGS boundaries](https://www.abs.gov.au/websitedbs/censushome.nsf/home/datapacks) (requires a free login) **IMPORTANT - download the ESRI Shapefile versions**
3. (optional) Download the 2016 [Indigenous](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.002) and [Non-ABS](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.003) boundaries as well
4. Unzip Census data and ASGS boundaries in the data/ directory of this repository
5. Run docker-compose: `docker-compose up`. The database will be built.
6. Use the constructed database as you wish.

If you want only the db running, do `docker-compose up db`. If you want to view the webapp, navigate to `localhost`, or the docker machine IP on (if you're doing Docker the old way!).

## Option 3 - Load PG_DUMP Files
Download Postgres dump files and restore them in your database.

Should take 15-30 minutes.

### Pre-requisites
- Postgres 9.6+ with PostGIS 2.2+
- A knowledge of [Postgres pg_restore parameters](https://www.postgresql.org/docs/9.6/static/app-pgrestore.html)

### Process
1. Download [census_2016_data.dmp](https://minus34.com/opendata/census-2016/census_2016_data.dmp) (~0.6Gb)
2. Download [census_2016_bdys.dmp](https://minus34.com/opendata/census-2016/census_2016_bdys.dmp) (~1.1Gb)
3. Download [census_2016_web.dmp](https://minus34.com/opendata/census-2016/census_2016_web.dmp) (~0.8Gb)
4. Edit the restore-census-schemas.bat or .sh script in the supporting-files folder for your database parameters and for the location of pg_restore
5. Run the script, come back in 15-30 minutes and enjoy!

### Data License

Source: [Australian Bureau of Statistics](https://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material)

## DATA CUSTOMISATION

- Display optimised tables are created by this process, They allow for web mapping from the state level down the SA1 level. These are created in the census web schema.
