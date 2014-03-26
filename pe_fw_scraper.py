#!/usr/bin/python2

#
# Use scraper on poweredgec.com to get latest firmware for C6220-2, 
# or whatever hw you're using.
#
# Hacked together by Erlend Bergsaas <erlend.bergsaas@met.no>
#   in March 2014.
#
# There is no exception handling worth mentioning here, by the way. :)
#

# Reads the following environment variables:
#  PE_FW_JSON    - The file from/to which json is read/written.
#  PE_FW_SCRAPER - Location of the scraper html site to be scraped.
#  PE_FW_LATEST  - Where you want the 'latest' file to be placed.
#  PE_FW_CACHE   - Target directory of downloaded ... stuff.
#  PE_FW_HW      - What hardware we're after.

import urllib2 # Deprecated in python3
import sgmllib # Deprecated in python3
import re
import os
import json
import subprocess
from optparse import OptionParser

def main():
  #  Parse the latest_PE_C_fw file. :)
  # http://docs.python.org/2/library/sgmllib.html

  pe_fw_scraper_url =  "http://www.poweredgec.com/latest_PE-C_fw.html"

  # For backwards compatibility. :)
  parser = OptionParser()
  parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False)
  parser.add_option("-S", "--silent", dest="silent", action="store_true", default=False)
  parser.add_option("-i", "--ignorecase", dest="ignorecase", action="store_true", default=False)
  parser.add_option("--json", dest="json", default=os.getenv("PE_FW_JSON", None))
  parser.add_option("--url", dest="url", default=os.getenv("PE_FW_SCRAPER", pe_fw_scraper_url))
  parser.add_option("--latest", dest="latest", default=os.getenv("PE_FW_LATEST", None))
  parser.add_option("--latest-prefix", dest="latest_prefix", default="")
  parser.add_option("--cache", dest="cache", default=os.getenv("PE_FW_CACHE", None))
  parser.add_option("--hw", dest="hw", default=os.getenv("PW_FW_HW", "C6220-2"))
  parser.add_option("-D", "--dump", dest="dump", action="append", default=[])
  parser.add_option("--no-header-info", dest="header_info", action="store_false", default=True)
  parser.add_option("--no-save-json", dest="save_json", action="store_false", default=True)
  parser.add_option("--retry-unknown-size", dest="retry_unknown_size", action="store_true", default=False)
  parser.add_option("--pattern", dest="pattern", default=None)
  parser.add_option("--exclude", dest="exclude", default=None)

  (opt, args) = parser.parse_args()


# http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
  # Download ''latest'' scraper result
  if bool(re.match(r".*://.*", opt.url)):
    if opt.verbose:
      msg("Extracting data from URL, using urllib: %s" %(opt.url))
    response = urllib2.urlopen(opt.url) 
  else:  
    if opt.verbose:
      msg("Extracting data from local file: %s" %(opt.url))
    response = open(opt.url, 'r')

  html = response.read()

  parser = ExtractLinks({'header': r"^%s" %(opt.hw)})


  # http://stackoverflow.com/questions/20199126/reading-a-json-file-using-python
  if opt.json and os.path.isfile(opt.json):
    if opt.verbose:
      msg("Reading JSON file from %s" %(opt.json))

    with open(opt.json) as json_file:
      parser.links = json.load(json_file)
  
    if 'json' in opt.dump:
      print json.dumps(parser.links, indent=2);
      exit(0)

    # Reset 'latest' sections
    for section,files in parser.links.items():
      for filename,details in files.items():
        details['Latest?'] = {}

  

  parser.feed(html)
  parser.close()

  # Read filesize/mtime for links
  if opt.header_info:
    if opt.verbose:
      msg("Fetching header information for files")
    header_info(parser.links, opt)
  
  # http://stackoverflow.com/questions/12309269/write-json-data-to-file-in-python
  if opt.json and opt.save_json:
    if opt.verbose:
      msg("Saving JSON file to %s" %(opt.json))
    with open(opt.json, 'w') as outfile:
      json.dump(parser.links, outfile)

  # Get a list of 'latest' entries.
  latest = []
  needs_download = []

  # compile pattern and exclude
  if opt.ignorecase:
    regopt = re.IGNORECASE
  else:
    regopt = 0
  if opt.pattern:
    pattern = re.compile(opt.pattern, regopt)
  else:
    pattern = False

  if opt.exclude:
    exclude = re.compile(opt.exclude, regopt)
  else:
    exclude = False
    

  for section,files in parser.links.items():
    for filename,details in files.items():
      # If 'pattern' doesn't match continue
      if pattern and not pattern.search(filename):
        continue

      # If 'exclude' matches, continue
      if exclude and exclude.search(filename):
        continue

      # If 'latest', add to latest list, to be written to file.
      if details['Latest?']['text'] == 'latest':
        latest.append(filename)

      if opt.cache:
        join = os.path.join(opt.cache, filename)
        if not os.path.isfile(join):
          needs_download.append([filename, details])
        else:
          if 'size' in details:
            try:
              size = int(details['size'])
              getsize = os.path.getsize(join)
              if size != getsize:
                print "Add %s to download again. Local filesize %d != remote filesize %d" %(filename,getsize, size)
                needs_download.append([filename, details])
            except ValueError:
              size = 0 # Assume ok on ValueError. :)


  if needs_download:
    if opt.verbose:
      msg("Will try and download %d files to cache %s" %(len(needs_download), opt.cache))
    for this in needs_download:
      try:
        curl_download(opt.cache, this[0], this[1], opt)
      except KeyboardInterrupt:
        break

  if opt.latest:
    if opt.verbose:
      msg("Saves ''latest'' file: %s" %(opt.latest))
    with open(opt.latest, 'w') as the_file:
      for line in latest:
        the_file.write("%s%s\n" %(opt.latest_prefix, line))

# http://stackoverflow.com/questions/4633162/sgml-parser-in-python
class ExtractLinks(sgmllib.SGMLParser):
  def __init__(self, opts, verbose=0):
    sgmllib.SGMLParser.__init__(self, verbose)
    
    self.header = re.compile(opts['header'])
    self.match_href = re.compile("^[^#].*$")
   
    self.opts = opts

    self.var = {
      'td': 0,
      'h2': None
    }
  
    self.context = {
      'td': False,
      'a': False,
      'fwtable': False,
      'th': False
    }

    self.links = {
    }

  def handle_data(self, data):
    if not self.context['fwtable']:
      return
    
    if self.context['th']:
      self.var['th_data'][self.var['th']].append(data)

    if self.context['td']:
      self.var['td_data'][self.var['td']].append(data)
    
    return

  def start_a(self, attrs):
    attrs = dict((x,y) for x,y in attrs)  
    if not self.context['fwtable']:
      return
    if not bool(self.match_href.match(attrs['href'])):
      return
    
    self.var['a_attrs'][self.var['td']] = attrs

  def start_h2(self, attrs):
    attrs = dict((x,y) for x,y in attrs)
    if not bool(self.header.match(attrs['id'])):
      self.var['h2'] = None
      return
    self.var['h2'] = attrs['id']

  def start_td(self, attrs):
    if not self.context['fwtable']:
      return
    self.context['td'] = True
    self.var['td'] += 1
    self.var['td_attrs'][self.var['td']] = dict((x,y) for x,y in attrs)
    self.var['td_data'][self.var['td']] = []

  def end_td(self):
    self.context['td'] = False

  def start_th(self, attrs):
    if not self.context['fwtable']:
      return
    self.context['th'] = True
    self.var['th'] += 1
    self.var['th_data'][self.var['th']] = []

  def end_th(self):
    self.context['th'] = False

  def start_table(self, attrs):
    attrs = dict((x,y) for x,y in attrs)
    if self.var['h2'] is None or attrs['class'] != 'fwtable':
      self.context['fwtable'] = False
      return
    
    self.context['fwtable'] = True
    self.var['th'], self.var['th_data'] = 0, {}
  
  def start_tr(self, attrs):
    if not self.context['fwtable']:
      return
    self.context['tr'] = True
    self.var['td'], self.var['td_attrs'], self.var['td_data']  = 0, {}, {}
    self.var['a_attrs'] = {}
    

  def end_tr(self):
    if not self.context['fwtable']:
      return
    self.context['tr'] = False
   
    if not self.var['h2'] in self.links:
      self.links[self.var['h2']] = {}

    row = {}
    filename = None

    # Do magic stuff with this row's data.
    #   One ''row''-entry per row, strange enough.
    for pos, header in self.var['th_data'].items():
      if not pos in self.var['td_data']:
        continue

      header=''.join(header).strip()
      td_data = ''.join(self.var['td_data'][pos]).strip()

      if header == 'Filename':
        filename = td_data

      td = {}
      if 'title' in self.var['td_attrs'][pos]:
        td['title'] = self.var['td_attrs'][pos]['title'].strip()
      
      if pos in self.var['a_attrs'] and 'href' in self.var['a_attrs'][pos]:
        td['href'] = self.var['a_attrs'][pos]['href'].strip()

      td['text'] = td_data
      row[header] = td

    if row:
      if filename in self.links[self.var['h2']]:
        previous_row = self.links[self.var['h2']][filename]

        # Same version, ok. Skip!
        if 'Ver' in row and 'Ver' in previous_row:
          if row['Ver']['text'] == previous_row['Ver']['text']:
            previous_row['Latest?'] = row['Latest?'] # Make sure latests is kept up to date
            return
        else:
          # UGh, dunno what to do.
          print "New version of filename %s. I'll overwrite the old entry." %(filename)
          self.links[self.var['h2']][filename] = row

      else:
        self.links[self.var['h2']][filename] = row

# msg
# Output messages in a "standardized format".
def msg(first, *x):
  print "*** %s" %(first)
  for line in x:
    print "    %s" %(line)

# Get some header info
def header_info(links, opt):
  try:
    # First count:
    total = 0
    for section, content in links.items():
      for filename, details in content.items():
        if 'size' in details:
          try: 
            size = int(details['size'])
            continue
          except ValueError:
            if not opt.retry_unknown_size:
              continue
            if not 'Filename' in details:
              continue
            if not 'href' in details['Filename']:
              continue
            total += 1
        else:
          total += 1
    thisno = 0
    for section, content in links.items():
      for filename, details in content.items():
        if 'size' in details:
          try:
            size = int(details['size'])
            continue
          except ValueError:
            if not opt.retry_unknown_size:
              continue
            if not 'Filename' in details:
              continue
            if not 'href' in details['Filename']:
              continue
            thisno += 1
        else:
          thisno +=1
        
        if opt.verbose:
          msg("(%d/%d) Fetching header info for %s from %s" %(
            thisno,
            total,
            filename,
            details['Filename']['href']
          ))
        # open session to url to get header info
        urlthing = urllib2.urlopen(details['Filename']['href'])

        # Server: Apache
        # ETag: "41dbece4aa15c1dd1345b8ae2367340e:1392133650"
        # Last-Modified: Tue, 11 Feb 2014 15:47:29 GMT
        # Accept-Ranges: bytes
        # Content-Length: 189
        # Content-Type: application/octet-stream
        # Date: Wed, 26 Mar 2014 09:04:41 GMT
        # Connection: close

        info = urlthing.info()

        if 'content-length' in info:
          links[section][filename]['size'] = info['content-length']
        else:
          links[section][filename]['size'] = 'UNKNOWN'

        if 'last-modified' in info:
          links[section][filename]['mtime'] = info['last-modified']
        else:
          links[section][filename]['mtime'] = 'UNKNOWN'

  except KeyboardInterrupt:
    return

# I gotta learn python. :)
# In ruby I'd do something like:
#  arr = arr + arr
def curl_download(cache,filename, details, opt):
  outfile = os.path.join(cache,filename)
  href = details['Filename']['href']
  if not opt.silent:
    msg("Try and download %s from %s" %(filename, href))
  curl='curl'
  curl_options = ['--location']
  if opt.silent:
    curl_options.append('--silent')
  return subprocess.call([curl]+curl_options+["--output", outfile, href])
# Run main.
main()

# vim:cc=80:noci:ai:ts=2:et
