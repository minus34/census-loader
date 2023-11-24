# census-loader
A quick way to get started with Australian Bureau of Statistics (ABS) Census 2021 data and boundaries. Note: Boundaries are available in both datums (GDA94 and GDA2020)

### There are 3 options for loading the data
1. [Run](https://github.com/minus34/census-loader#option-1---run-load-censuspy) the load-census Python script and build the database schemas in a single step **on a Mac or Linux machine**
2. [Pull](https://github.com/minus34/census-loader#option-2---run-the-database-in-a-docker-container) the database from Docker Hub and run it in a container
3. [Download](https://github.com/minus34/census-loader#option-3---load-pg_dump-files) the Postgres dump files and restore them in your database.

## Option 1 - Run load-census.py
Running the Python script takes 15-30 minutes on a Postgres server (or desktop) configured for performance.

### Performance
To get a good load time you'll need to configure your Postgres server for performance. There's a good guide [here](https://revenant.ca/www/postgis/workshop/tuning.html), noting its old and the memory parameters can be beefed up if you have the RAM.

### Pre-requisites
- Postgres 14+ with PostGIS 3.2+ (tested on 14.10 on macOS Sonoma)
- Add the Postgres bin directory to your system PATH
- Python 3.6+ with Psycopg 3 & Pandas packages installed

### Process
1. Run the `xx_run_all.sh` script in the `supporting-files/processing` folder. It will download the data and boundary files from the ABS and import them into Postgres in a single step.
2. Come back in 15-30 minutes and enjoy!

Alternately - you can download the files manually yourself, import the boundary Shapefiles or GeoPackages using GDAL and then import the data using the main script `load-census.py`.

### load-census.py Command Line Options
The behaviour of the main census-loader script can be controlled by specifying various command line options to the script. Supported arguments are:

#### Required Arguments
* `--census-data-path` specifies the path to the extracted Census metadata and data tables (eg *.xlsx and *.csv files). __This directory must be accessible by the Postgres server__, and the corresponding local path for the server to this directory may need to be set via the `local-server-dir` argument

#### Postgres Parameters
* `--pghost` the host name for the Postgres server. This defaults to the `PGHOST` environment variable if set, otherwise defaults to `localhost`.
* `--pgport` the port number for the Postgres server. This defaults to the `PGPORT` environment variable if set, otherwise `5432`.
* `--pgdb` the database name for Postgres server. This defaults to the `PGDATABASE` environment variable if set, otherwise `geo`.
* `--pguser` the username for accessing the Postgres server. This defaults to the `PGUSER` environment variable if set, otherwise `postgres`.
* `--pgpassword` password for accessing the Postgres server. This defaults to the `PGPASSWORD` environment variable if set, otherwise `password`.

#### Optional Arguments
* `--data-schema` schema name to store Census data tables in. Defaults to `census_2021_data`. **You will need to change this argument if you set `--census-year=2011`**
* `--max-processes` specifies the maximum number of parallel processes to use for the data load. Set this to the number of cores on the Postgres server minus 2, but limit to 12 if 16+ cores - there is minimal benefit beyond 12. Defaults to 3.

### Example Command Line Arguments
`python load-census.py --census-data-path="C:\temp\census_2021_data"`

Loads the 2021 Census data using a maximum of 4 parallel processes (the default) into the default schema. Census data archives have been extracted to the folder `C:\temp\census_2021_data`.

`python load-census.py --max-processes=8 --data-schema=census_2021_stats --census-data-path="C:\temp\census_2011_data"`

Loads the 2021 Census data using a maximum of 8 parallel processes into a renamed schema. Census data archives have been extracted to the folder `C:\temp\census_2011_data`.

### Attribution
When using the resulting data from this process - you will need to adhere to the ABS data attribution requirements for the [Census and ASGS data](https://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material), as per the Creative Commons (Attribution) license.

### WARNING:
- The scripts will DROP ALL TABLES and recreate them using CASCADE; meaning you'll LOSE YOUR VIEWS if you have created any! If you want to keep the existing data - you'll need to change the schema names in the script or use a different database

### IMPORTANT:
- Whilst you can choose which schema to load the data into, I haven't QA'd the permutations. Stick with the defaults if you have limited Postgres experience 

## Option 2 - Run the database in a docker container
Download and run a Docker container with Census data and ASGS boundaries ready to go in a Postgres database.

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
- Postgres 14+ with PostGIS 3.2+
- A knowledge of [Postgres pg_restore parameters](https://www.postgresql.org/docs/9.6/static/app-pgrestore.html)

### Process
1. Download [census_2021_data.dmp](https://minus34.com/opendata/census-2021/census_2021_data.dmp) (~1.1Gb)
2. Download [census_2021_bdys_gda94.dmp](https://minus34.com/opendata/census-2021/census_2021_bdys_gda94.dmp) or [census_2021_bdys_gda2020.dmp](https://minus34.com/opendata/census-2021/census_2021_bdys_gda2020.dmp) (~1.5Gb)
3. Edit the `restore-census-schemas.bat` or 'restore-census-schemas.sh' script in the 'supporting-files' folder for your database parameters and for the location of pg_restore
4. Run the script, come back in 15-30 minutes and enjoy!

### Data License

Source: [Australian Bureau of Statistics](https://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material)
