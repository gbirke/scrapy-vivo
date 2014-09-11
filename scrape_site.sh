#!/bin/sh

NAME=$1

GLOB="${NAME}*.csv"
if test -n "$(find . -maxdepth 1 -name '$GLOB' -print -quit)";then
    rm -f /home/birkeg/tmp/scraperesult/csv/$GLOB
fi
 

scrapy crawl -o "/home/birkeg/tmp/scraperesult/csv/${NAME}_%(item_name)s.csv" -t csv "${NAME}_spider"