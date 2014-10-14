#!/bin/sh

NAME=$1
OUTPUT_DIR=/home/birkeg/opensciencelab/vivo-toolchain/trunk/var

GLOB="${NAME}*.csv"
find $OUTPUT_DIR -maxdepth 1 -name "$GLOB" -delete

scrapy crawl -o "$OUTPUT_DIR/${NAME}_%(item_name)s.csv" -t csv "${NAME}_spider"