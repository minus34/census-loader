# census-loader
A quick way to get started with Australian Bureau of Statistics (ABS) Census 2011 or 2016 data

### There are 3 options for loading the data
1. [Run](https://github.com/minus34/census-loader#option-1---run-loadgnafpy) the load-census Python script and build the database schemas in a single step
2. [Build](https://github.com/minus34/census-loader#option-2---build-the-database-in-a-docker-environment) the database in a docker environment
3. [Download](https://github.com/minus34/census-loader#option-3---load-pg_dump-files) the Census Postgres dump files and restore them in your database. __Note: Census 2016 data and ASGS boundaries only__

## Option 1 - Run load-census.py
Running the Python script takes 10-15 minutes on a Postgres server configured for performance.

My benchmarks are:
- 3 year old, 32 core Windows server with SSDs = 10 mins
- MacBook Pro = 15 mins

### Performance
To get a good load time you'll need to configure your Postgres server for performance. There's a good guide [here](http://revenant.ca/www/postgis/workshop/tuning.html), noting it's a few years old and some of the memory parameters can be beefed up if you have the RAM.

### Pre-requisites
- Postgres 9.6+ with PostGIS 2.2+ (tested on 9.6 on macOS Sierra & Windows 10)
- Add the Postgres bin directory to your system PATH
- Python 3.x with Psycopg2 2.6+

### Process
1. Download [ABS Census 2016 CSV Files](http://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/2079.02016)
2. Download [ABS 2016 Australian Statistical Geography Standard (ASGS) boundaries](http://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/1270.0.55.001July%202016) (**download the ESRI Shapefile versions**)
3. Unzip the Census CSV files to a directory on your Postgres server
4. Alter security on the directory to grant Postgres read access
5. Unzip the ASGS boundaries to a local directory
6. Create the target database (if required)
7. Check the optional and required arguments by running load-census.py with the `-h` argument (see command line examples below)
8. Run the script, come back in 10-15 minutes and enjoy!

### Command Line Options
The behaviour of census-loader can be controlled by specifying various command line options to the script. Supported arguments are:

#### Required Arguments
* `--census-data-path` specifies the path to the extracted Census metadata and data tables (eg *.xlsx and *.csv files). __This directory must be accessible by the Postgres server__, and the corresponding local path for the server to this directory may need to be set via the `local-server-dir` argument
* `--local-server-dir` specifies the local path on the Postgres server corresponding to `census-data-path`. If the server is running locally this argument can be omitted.
* `--census-bdys-path` specifies the path to the extracted ASGS boundary files. Unlike `census-data-path`, this path does not necessarily have to be accessible to the remote Postgres server.

#### Postgres Parameters
* `--pghost` the host name for the Postgres server. This defaults to the `PGHOST` environment variable if set, otherwise defaults to `localhost`.
* `--pgport` the port number for the Postgres server. This defaults to the `PGPORT` environment variable if set, otherwise `5432`.
* `--pgdb` the database name for Postgres server. This defaults to the `PGDATABASE` environment variable if set, otherwise `psma_201602`.
* `--pguser` the username for accessing the Postgres server. This defaults to the `PGUSER` environment variable if set, otherwise `postgres`.
* `--pgpassword` password for accessing the Postgres server. This defaults to the `PGPASSWORD` environment variable if set, otherwise `password`.

#### Optional Arguments
* `--census-year` Year of the ABS Census data to load. Valid values are `2011` and `2016` Defaults to `2016`.
* `--raw-gnaf-schema` schema name to store raw GNAF tables in. Defaults to `raw_gnaf_<census_year>`.
* `--raw-admin-schema` schema name to store raw admin boundary tables in. Defaults to `raw_admin_bdys_<census_year>`.
* `--max-processes` specifies the maximum number of parallel processes to use for the data load. Set this to the number of cores on the Postgres server minus 2, but limit to 12 if 16+ cores - there is minimal benefit beyond 12. Defaults to 3.

### Example Command Line Arguments
* Local Postgres server: `python load-census.py --census-data-path="C:\temp\census_2016_data" --census-bdys-path="C:\temp\census_2016_boundaries"` Loads the Census data to a Postgres server running locally. Census data archives have been extracted to the folder `C:\temp\census_2016_data`, and ASGS boundaries have been extracted to the `C:\temp\census_2016_boundaries` folder.
* Remote Postgres server: `python load-census.py --census-data-path="\\svr\shared\census_2016_data" --local-server-dir="F:\shared\census_2016_data" --census-bdys-path="C:\temp\census_2016_boundaries"` Loads the Census data which have been extracted to the shared folder `\\svr\shared\census_2016_data`. This shared folder corresponds to the local `F:\shared\census_2016_data` folder on the Postgres server. ASGS boundaries have been extracted to the `C:\temp\census_2016_boundaries` folder.

### Attribution
When using the resulting data from this process - you will need to adhere to the ABS data attribution requirements for the [Census and ASGS data](http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material), as per the Creative Commons (Attribution) license.

### WARNING:
- The scripts will DROP ALL TABLES and recreate them using CASCADE; meaning you'll LOSE YOUR VIEWS if you have created any! If you want to keep the existing data - you'll need to change the schema names in the script or use a different database

### IMPORTANT:
- Whilst you can choose which 2 schemas to load the data into, I haven't QA'd all permutations. Stick with the defaults if you have limited Postgres experience 
- If you're not running the Python script on the Postgres server, you'll need to have access to a network path to the Census data files on the database server (to create the list of files to process). The alternative is to have a local copy of the CSV files

## Option 2 - Build the database in a docker environment

Create a Docker container with GNAF and the Admin Bdys ready to go, so they can be deployed anywhere.

### Process
1. Download [ABS Census 2016 CSV Files](http://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/2079.02016)
2. Download [ABS 2016 ASGS boundaries](http://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/1270.0.55.001July%202016) (**download the ESRI Shapefile versions**)
3. Unzip Census data and ASGS boundaries in the data/ directory of this repository
4. Run docker-compose: `docker-compose up`. The database will be built.
5. Use the constructed database as you wish.

## Option 3 - Load PG_DUMP Files
Download Postgres dump files and restore them in your database.

Should take 15 minutes.

### Pre-requisites
- Postgres 9.6+ with PostGIS 2.2+
- A knowledge of [Postgres pg_restore parameters](http://www.postgresql.org/docs/9.6/static/app-pgrestore.html)

### Process
1. Download [census-boundaries-2016.dmp](http://minus34.com/opendata/census-2016/census-data-2016.dmp) (~1.6Gb)
2. Download [census-boundaries-2016.dmp](http://minus34.com/opendata/census-2016/census-boundaries-2016.dmp) (~2.0Gb)
3. Edit the restore-gnaf-admin-bdys.bat or .sh script in the supporting-files folder for your database parameters and for the location of pg_restore
5. Run the script, come back in 15-60 minutes and enjoy!

### Data Licenses

Incorporates or developed using G-NAF ©PSMA Australia Limited licensed by the Commonwealth of Australia under the [Open Geo-coded National Address File (G-NAF) End User Licence Agreement](http://data.gov.au/dataset/19432f89-dc3a-4ef3-b943-5326ef1dbecc/resource/09f74802-08b1-4214-a6ea-3591b2753d30/download/20160226---EULA---Open-G-NAF.pdf).

Incorporates or developed using Administrative Boundaries ©PSMA Australia Limited licensed by the Commonwealth of Australia under [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

## DATA CUSTOMISATION
GNAF and the Admin Bdys have been customised to remove some of the known, minor limitations with the data. The most notable are:
- All addresses link to a gazetted locality that has a boundary. Those small number of addresses that don't in raw GNAF have had their locality_pid changed to a gazetted equivalent
- Localities have had address and street counts added to them
- Suburb-Locality bdys have been flattened into a single continuous layer of localities - South Australian Hundreds have been removed and ACT districts have been added where there are no gazetted localities
- The Melbourne, VIC locality has been split into Melbourne, 3000 and Melbourne 3004 localities (the new locality PIDs are VIC 1634_1 & VIC 1634_2). The split occurs at the Yarra River (based on the postcodes in the Melbourne addresses)
- A postcode boundaries layer has been created using the postcodes in the address tables. Whilst this closely emulates the official PSMA postcode boundaries, there are several hundred addresses that are in the wrong postcode bdy. Do not treat this data as authoritative

