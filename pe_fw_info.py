#!/usr/bin/python2

#
# Use scraper on poweredgec.com to get latest firmware for C6220-2, 
# or whatever hw you're using.
#
# Hacked together by Erlend Bergsaas <erlend.bergsaas@met.no>
#   in March 2014.
#
# There is no exception handling worth mentioning here, by the way. :)

# Reads the following environment variables:
#  PE_FW_JSON    - The file from/to which json is read/written.
#  PE_FW_SCRAPER - Location of the scraper html site to be scraped.
#  PE_FW_LATEST  - Where you want the 'latest' file to be placed.
#  PE_FW_CACHE   - Target directory of downloaded ... stuff.
#  PE_FW_HW      - What hardware we're after.

import re
import os
import json
from optparse import OptionParser

def msg(first,*x):
  print "*** %s" %(first)
  for line in x:
    print "    %s" %(line)


parser = OptionParser()
parser.add_option("--json", dest="json", default=os.getenv("PE_FW_JSON", None))
parser.add_option("-i", "--ignore-case", dest="ignorecase", action="store_true", default=False)
#  parser 

(opt, args) = parser.parse_args()

if not opt.json:
  msg("NOthing to do: no json file specified")
  exit(1)
with open(opt.json) as json_file:
  data = json.load(json_file)
  

first = True
if len(args) == 0:

  order = ["Rel Date", "Filename", "Importance", "Ver", "Latest?", "DUP?", "Description"]
  for section, files in data.items():
    maxlen={}
    # Make nice columns. :)
    if first:
      first = False
    else:
      print ""

    msg("Type: %s" %(section))
    for filename, details in files.items():
      for name, data in details.items():
        if isinstance(data, dict) and 'text' in data:
          datalen = len(data['text'])
          if not name in maxlen:
            maxlen[name] = datalen
          else:
            if maxlen[name] < datalen:
              maxlen[name] = datalen

    #1 Rel Date, 
    #2   Filename 
    #3     Importance 
    #4       Ver 
    #5         Latest? 
    #6           DUP? 
    #7             Description
    for filename, details in files.items():
      fmt = []
      for key in order:
        fmt += [maxlen[key], details[key]['text']]

#      for key, asterix in maxlen.items():
#        fmt += [asterix, details[key]['text']]
      print "\t".join(["%-*s"]*7) % tuple(fmt)

    print ""
else:
  for argname in args:
    if opt.ignorecase:
      reopt = re.IGNORECASE
    else:
      reopt = 0
    
    argsearch = re.compile(r"%s" %(argname), reopt)

    for section, files in data.items():
      for filename, details in files.items():
        if not bool(argsearch.search(filename)):
          continue

        if first:
          first = False
        else:
          print ""

        msg("%s: %s" %(section, filename))
        maxlen = 0
        for key, value in details.items():
          keylen = len(key)
          if maxlen < keylen:
            maxlen = keylen
        for key, value in details.items():
          if isinstance(value, dict):
            text = value['text']
            if 'href' in value:
              href = value['href']
            else:
              href = None
          else:
            text = value
            href = None
          print("     %-*s %s" %(maxlen, key, text))
          if href:
            print("     %-*s %s" %(maxlen, "", href))
