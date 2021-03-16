#!/bin/bash

# Start all services
cd docker/projects/planet
pelias compose up

cd ../../../openrouteservice/docker
docker-compose up -d

cd ../../api
source apienv/Scripts/activate
python3 run.py


# # uncomment to build from scratch (also comment out start code above)
# # git clone https://github.com/GIScience/openrouteservice.git
# set -x

# # clone this repository
# git clone https://github.com/pelias/docker.git && cd docker

# # install pelias script
# # this is the _only_ setup command that should require `sudo`
# sudo ln -s "$(pwd)/pelias" /usr/local/bin/pelias

# # cd into the project directory
# cd projects/planet

# # create a directory to store Pelias data files
# # see: https://github.com/pelias/docker#variable-data_dir
# # note: use 'gsed' instead of 'sed' on a Mac
# mkdir ./data
# sed -i '/DATA_DIR/d' .env
# echo 'DATA_DIR=./data' >> .env

# # run build
# pelias compose pull
# pelias elastic start
# pelias elastic wait
# pelias elastic create
# pelias download all
# pelias prepare all
# pelias import all
# pelias compose up





















