## Requirements
1. Conda (or miniconda) installed = https://docs.conda.io/en/latest/miniconda.html

## Setup
1. Create conda environment: `conda env create -f environment.yml`
2. Activate conda environment `conda activate python-ip-lookup`

## Run
1. On your terminal: `python ip_lookup.py $FILE_TO_SEARCH`
   1. Replace `$FILE_TO_SEARCH` with the file path you wish to search.
2. The file `output.json` will be created containing the lookup result 

## Utils
1. If any changes are made on `environment.yml` you should update the environment with the following command:
`conda env update --file environment.yml  --prune`
2. A `http_cache.sqlite` file will be created. This file is used to cache HTTPS requests made to perform the lookup.
