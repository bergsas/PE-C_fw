#!/bin/bash
if [ "$1" = "-e" ]
then
  echoonly=1
  shift
else
  echoonly=
fi

for n in "$@"
do
  iso="`unzip -l "$n" 2>/dev/null | 
    ruby -lne 'next unless $_ =~ /\.iso/i; puts $_.split(nil,4)[3]'`"
  if [ -z "$iso" ]
  then
    echo "$n: No iso found" 1>&4
  else
    echo "$n: Found iso $iso"
  fi

  [ "$echoonly" ] && continue

  isoname="${iso##*/}"
  
  if ! (
    set -x
    unzip -p "$n" "$iso" > "$isoname"
  )
  then
    exit $?
  fi

done
