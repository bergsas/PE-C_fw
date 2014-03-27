#!/bin/bash

find=find

if [ -z "$1" ] || [ "$1" = "--" ]
then
  if [ "$1" == "--" ]
  then
    shift
  fi
  echo + sudo dmidecode -s system-serial-number
  if tag="`sudo dmidecode -s system-serial-number`"
  then
    if [ -z "$tag" ]
    then
      echo "$0: no tag returned."
      exit 1
    fi
    "$0" "$tag" "$@"
    exit $?
  fi
  exit
fi

if [ -z "$DRIVERSDATA" ]
then
  DRIVERSDATA=driversdata-scraper.py
  if [ -z "`which "$DRIVERSDATA"`" ]
  then
    for p in bin ../bin
    do
      if [ -e "$p/$DRIVERSDATA" ]
      then
        DRIVERSDATA="$p/$DRIVERSDATA"
      fi
    done
  fi
fi
[ -z "$DRIVERSDATA" ] && DRIVERSDATA=.driversdata-scraper.py
[ -z "$DRIVERSDATA_CACHE" ] &&  DRIVERSDATA_CACHE="cache"
[ -z "$DRIVERSDATA_LATEST" ] && DRIVERSDATA_LATEST="$DRIVERSDATA_CACHE/latest-$1.txt"
[ -z "$DRIVERSDATA_LATEST_PREFIX" ] && DRIVERSDATA_LATEST_PREFIX=""
[ -z "$DRIVERSDATA_HTML_CACHE" ] && DRIVERSDATA_HTML_CACHE="$DRIVERSDATA_CACHE/tag-$1.html"

set | grep ^DRIVERSDATA
shift
# Do stuff. :)
[ ! -d "$DRIVERSDATA_CACHE" ] && mkdir "$DRIVERSDATA_CACHE"
if [ ! -e "$DRIVERSDATA_HTML_CACHE" ] || [ -z "`"$find" "$DRIVERSDATA_HTML_CACHE" -mmin -60`" ] 
then
  if ! "$DRIVERSDATA" -A "$1" -o savehtml="$DRIVERSDATA_HTML_CACHE" -L "$DRIVERSDATA_LATEST" -P "$DRIVERSDATA_LATEST_PREFIX" -C "$DRIVERSDATA_CACHE" -d "$@"
  then
    exit $?
  fi
else
  echo "*** Running using cached HTML: $DRIVERSDATA_HTML_CACHE"
   if ! "$DRIVERSDATA" -U "$DRIVERSDATA_HTML_CACHE" -L "$DRIVERSDATA_LATEST" -P "$DRIVERSDATA_LATEST_PREFIX" -C "$DRIVERSDATA_CACHE" -d "$@"
  then
    exit $?
  fi
fi
# Run like this:
#  DRIVERSDATA=../bin/driversdata-scraper.py DRIVERSDATA_CACHE=cache ./scrape-c6220-2-bin.sh
