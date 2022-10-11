#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------------------------------

ENV_NAME=geo
PYTHON_VERSION="3.10"

# --------------------------------------------------------------------------------------------------------------------

echo "-------------------------------------------------------------------------"
echo "Creating new Conda Environment '${ENV_NAME}'"
echo "-------------------------------------------------------------------------"

# deactivate current environment and start base env (in case you just deactivated it) - lazy method
conda deactivate
conda activate base

# WARNING - removes existing environment
conda env remove --name ${ENV_NAME}

# clear cache (builds over time)
conda clean -y --all

# update Conda base environment
conda update -y conda

# Create Conda environment
conda create -y -n ${ENV_NAME} python=${PYTHON_VERSION}

# activate and setup env
conda activate ${ENV_NAME}
conda env config vars set JAVA_HOME="/usr/local/opt/openjdk@11"
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict

# reactivate for env vars to take effect
conda activate ${ENV_NAME}

## install Mamba (faster package installer)
#conda install -y -c conda-forge mamba

# install geospatial packages
conda install -y -c conda-forge gdal pygeos pyarrow dask-geopandas openpyxl psycopg geoalchemy2 rasterio boto3
conda activate ${ENV_NAME}

# --------------------------
# extra bits
# --------------------------

## activate env
#conda activate ${ENV_NAME}

## shut down env
#conda deactivate

## delete env permanently
#conda env remove --name ${ENV_NAME}
