#!/bin/bash

export AZURE_TESTING=1

pip install -vv git+https://github.com/NSLS-II-ISS/isstools@main
pip install -vv git+https://github.com/NSLS-II-ISS/xas@main
pip install -vv git+https://github.com/NSLS-II-ISS/isscloudtools@master "oauth2client<4.0.0"
pip install -vv git+https://github.com/NSLS-II-ISS/xview@main

# Add a non-standard 'iss-local.yml' databroker config:
cp -v $HOME/.config/databroker/iss.yml $HOME/.config/databroker/iss-local.yml

# Create non-standard directories:
sudo mkdir -v -p /nsls2/xf08id/metadata/

sudo chmod -Rv go+rw /nsls2/xf08id/

# touch /nsls2/xf08id/...

