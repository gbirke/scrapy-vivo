#!/bin/sh

apt-get update

# Install dependencies for python libraries
apt-get -y install build-essential libssl-dev libffi-dev libxml2 libxml2-dev libxslt-dev

# Install python and PIP
apt-get -y install python python-dev python-pip

# install version control programs
apt-get -y install subversion git

VIVO_DIR=/usr/local/vivo2014

mkdir -p $VIVO_DIR
chown vagrant:vagrant $VIVO_DIR
cd $VIVO_DIR

# Folgende Befehle wg. fehlendem SSH-key müssen manuell ausgeführt werden

#git clone git@github.com:gbirke/scrapy-vivo.git .
#pip install -r requirements.txt


