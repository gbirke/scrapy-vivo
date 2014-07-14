#!/bin/sh

apt-get update

apt-get -y install python python-pip

apt-get -y install subversion git

cd /media/vivo_2014

#svn checkout https://sysadmin.tib.uni-hannover.de/svn/opensciencelab/vivo-scrapy/trunk/vivo_2014 .

pip install -r requirements.txt


