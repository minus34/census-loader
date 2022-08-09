#!/usr/bin/env bash

# SETUP - download Git repo and build locally (requires Java and Maven)
cd ${GIT_HOME}
mkdir -p eurostat
cd eurostat
git clone https://github.com/eurostat/RegionSimplify.git
cd RegionSimplify
mvn package


# mkdir -p test_out

# "ASGS_2021_Main_Structure_GDA2020" "ASGS_Ed3_2021_Indigenous_Structure_GDA2020"

for dataset in "ASGS_Ed3_2021_Non_ABS_Structures_GDA2020"
do
	for scaleM in "5" "10"
	do
    	echo "Generalisation for "$dataset" - 1:"$scaleM"000000"
		java -Xmx8g -Xms4g -jar ./target/RegionSimplify-1.4.0-SNAPSHOT.jar -i "/Users/s57405/tmp/census_2021_bdys/"$dataset".gpkg" -o "/Users/s57405/tmp/census_2021_bdys/thinned/"$dataset"-"$scaleM"M.gpkg" -s $scaleM"000000"
	done
done



java -Xmx8g -Xms4g -jar /Users/s57405/Downloads/RegionSimplify/target/RegionSimplify-1.4.0-SNAPSHOT.jar \
-i "/Users/s57405/tmp/census_2021_bdys/ASGS_2021_Main_Structure_GDA2020.gpkg" \
-o "/Users/s57405/tmp/census_2021_bdys/thinned/test.gpkg"


java -Xmx8g -Xms4g -jar /Users/s57405/Downloads/RegionSimplify/target/RegionSimplify-1.4.0-SNAPSHOT.jar \
-i "/Users/s57405/tmp/census_2021_bdys/test.shp" \
-o "/Users/s57405/tmp/census_2021_bdys/thinned/test.shp"


