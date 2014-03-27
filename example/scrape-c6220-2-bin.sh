#!/bin/bash
#../bin/driversdata-scraper.py -U ../c6220-2-drivers.html

curl="curl"
find=find

[ -z "$DRIVERSDATA" ] && DRIVERSDATA=bin/driversdata-scraper.py
[ -z "$DRIVERSDATA_CACHE" ] &&  DRIVERSDATA_CACHE="/srv/ftp/fw/c6220-2"
[ -z "$DRIVERSDATA_LATEST" ] && DRIVERSDATA_LATEST="$DRIVERSDATA_CACHE/latest_bin.txt"
[ -z "$DRIVERSDATA_LATEST_PREFIX" ] && DRIVERSDATA_LATEST_PREFIX=""
[ -z "$DRIVERSDATA_HTML_CACHE" ] && DRIVERSDATA_HTML_CACHE="$DRIVERSDATA_CACHE/c6220-2-dump.html"
[ -z "$DRIVERSDATA_URL" ] && DRIVERSDATA_URL="http://www.dell.com/support/home/us/en/04/product-support/product/poweredge-c6220-2/drivers"

#set | grep ^DRIVERSDATA

# If cache file doesn't exist or if it is more than 24 hours old, 
#   (re-)fetch
if [ ! -e "$DRIVERSDATA_HTML_CACHE" ] || 
  [ -z "`"$find" "$DRIVERSDATA_HTML_CACHE" -mtime -1`" ]
then
  if ! "$curl" -SsLo "$DRIVERSDATA_HTML_CACHE" "$DRIVERSDATA_URL"
  then
    exit 1
  fi
fi

# Do stuff. :)
if ! "$DRIVERSDATA" -U "$DRIVERSDATA_HTML_CACHE" -L "$DRIVERSDATA_LATEST" -P "$DRIVERSDATA_LATEST_PREFIX" -C "$DRIVERSDATA_CACHE" -iF "bin$" -ds
then
  exit $?
fi

# Run like this:
#  DRIVERSDATA=../bin/driversdata-scraper.py DRIVERSDATA_CACHE=cache ./scrape-c6220-2-bin.sh
