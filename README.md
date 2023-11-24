# census-loader
A quick way to get started with Australian Bureau of Statistics (ABS) Census 2021 data; as well as Census 2016 or 2011 data.

### There are 3 options for loading the data
1. [Run](https://github.com/minus34/census-loader#option-1---run-loadcensuspy) the load-census Python script and build the database schemas in a single step
2. [Build](https://github.com/minus34/census-loader#option-2---build-the-database-in-a-docker-environment) the database in a docker environment.
3. [Download](https://github.com/minus34/census-loader#option-3---load-pg_dump-files) the Postgres dump files and restore them in your database.

## Option 1 - Run load-census.py
Running the Python script takes 15-30 minutes on a Postgres server (or dekstop) configured for performance.

### Performance
To get a good load time you'll need to configure your Postgres server for performance. There's a good guide [here](https://revenant.ca/www/postgis/workshop/tuning.html), noting it's old and some of the memory parameters can be beefed up if you have the RAM.

### Pre-requisites
- Postgres 14+ with PostGIS 3.x+ (tested on 14.10 on macOS Sonoma)
- Add the Postgres bin directory to your system PATH
- Python 3.x with Psycopg, xlrd & Pandas packages installed

### Process
1. Download [ABS Census DataPacks](https://datapacks.censusdata.abs.gov.au/datapacks/)
2. Download [ABS 2021 ASGS boundaries](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.001) or [ABS 2011 ASGS boundaries](https://www.abs.gov.au/websitedbs/censushome.nsf/home/datapacks) (requires a free login) **IMPORTANT - download the ESRI Shapefile versions**
3. (optional) Download the 2021 [Indigenous](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.002) and [Non-ABS](https://www.abs.gov.au/ausstats/abs@.nsf/mf/1270.0.55.003) boundaries as well
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
* `--pgdb` the database name for Postgres server. This defaults to the `PGDATABASE` environment variable if set, otherwise `geo`.
* `--pguser` the username for accessing the Postgres server. This defaults to the `PGUSER` environment variable if set, otherwise `postgres`.
* `--pgpassword` password for accessing the Postgres server. This defaults to the `PGPASSWORD` environment variable if set, otherwise `password`.

#### Optional Arguments
* `--census-year` year of the ABS Census data to load. Valid values are `2011`, `2016` and `2021` Defaults to `2021`.
* `--data-schema` schema name to store Census data tables in. Defaults to `census_2021_data`. **You will need to change this argument if you set `--census-year=2011`**
* `--boundary-schema` schema name to store Census boundary tables in. Defaults to `census_2021_bdys_<gda94 or gda20202>`. **You will need to change this argument if you set `--census-year=2011`**
* `--web-schema` schema name to store Census boundary tables in. Defaults to `census_2021_web`. **You will need to change this argument if you set `--census-year=2011`**
* `--max-processes` specifies the maximum number of parallel processes to use for the data load. Set this to the number of cores on the Postgres server minus 2, but limit to 12 if 16+ cores - there is minimal benefit beyond 12. Defaults to 3.

### Example Command Line Arguments
`python load-census.py --census-data-path="C:\temp\census_2021_data" --census-bdys-path="C:\temp\census_2021_boundaries"`

Loads the 2021 Census data using a maximum of 3 parallel processes into the default schemas. Census data archives have been extracted to the folder `C:\temp\census_2021_data`, and ASGS boundaries have been extracted to the `C:\temp\census_2021_boundaries` folder.

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
1. In your docker environment pull the image using `docker pull minus34/censusloader:latest`
2. Run using `docker run --publish=5433:5432 minus34/censusloader:latest`
3. Access Postgres in the container via port `5433`. Default login is - user: `postgres`, password: `password`

*Note: the compressed Docker image is 8Gb, uncompressed is 27Gb*

**WARNING: The default postgres superuser password is insecure and should be changed using:**

`ALTER USER postgres PASSWORD '<something a lot more secure>'`

## Option 3 - Load PG_DUMP Files
Download Postgres dump files and restore them in your database.

Should take 15-30 minutes.

### Pre-requisites
- Postgres 9.6+ with PostGIS 2.2+
- A knowledge of [Postgres pg_restore parameters](https://www.postgresql.org/docs/9.6/static/app-pgrestore.html)

### Process
1. Download [census_2021_data.dmp](https://minus34.com/opendata/census-2021/census_2021_data.dmp) (~0.6Gb)
2. Download [census_2021_bdys_gda94.dmp](https://minus34.com/opendata/census-2021/census_2021_bdys_gda94.dmp) (~1.1Gb)
3. Edit the restore-census-schemas.bat or .sh script in the supporting-files folder for your database parameters and for the location of pg_restore
4. Run the script, come back in 15-30 minutes and enjoy!

### Data License

Source: [Australian Bureau of Statistics](https://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material)

## DATA CUSTOMISATION

- Display optimised tables are created by this process, They allow for web mapping from the state level down the SA1 level. These are created in the census web schema.
