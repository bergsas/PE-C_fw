#!/usr/bin/python2

#
# Use scraper on poweredgec.com to get latest firmware for C6220-2, 
# or whatever hw you're using.
#

import urllib2 # Deprecated in python3
import sgmllib # Deprecated in python3

import re
import os

def main():
  #  Parse the latest_PE_C_fw file. :)
  # http://docs.python.org/2/library/sgmllib.html


  pe_c_fw_scraper_url =  "http://www.poweredgec.com/latest_PE-C_fw.html"
  pe_c_fw_scraper = os.getenv("PE_C_FW_SCRAPER", pe_c_fw_scraper_url)

  # http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
  # Download ''latest'' scraper result
  if bool(re.match(r".*://.*", pe_c_fw_scraper)):
    response = urllib2.urlopen(pe_c_fw_scraper) 
  else:  
    response = open(pe_c_fw_scraper, 'r')

  html = response.read()

  parser = ExtractLinks({'header': r"^C6220-2"})
  parser.feed(html)
  parser.close()

  for section, array in parser.links.items():
    for fil in array:
      print fil['Filename']['href'];
      # HTTP/1.1 200 OK
      # Server: Apache
      # ETag: "9aeff4be0aafe91c156027d82173c2a7:1381436049"
      # Last-Modified: Thu, 10 Oct 2013 20:14:09 GMT
      # Accept-Ranges: bytes
      # Content-Length: 11798088
      # Content-Type: application/octet-stream
      # Date: Tue, 25 Mar 2014 21:45:17 GMT
      # Connection: keep-alive

      #urlthing = urllib2.urlopen(fil['Filename']['href'])
      #print urlthing.info() 
      parser.links[section]
      


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
    
    if self.context['a']:
      self.var['a_data'][self.var['td']].append(data)
    
    
    return

  def start_a(self, attrs):
    attrs = dict((x,y) for x,y in attrs)  
    if not self.context['fwtable']:
      return
    if not bool(self.match_href.match(attrs['href'])):
      return
    
    self.var['a_attrs'][self.var['td']] = attrs
    self.var['a_data'][self.var['td']] = []

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
    self.var['a_attrs'], self.var['a_data'] = {}, {}
    

  def end_tr(self):
    if not self.context['fwtable']:
      return
    self.context['tr'] = False
   
    if not self.var['h2'] in self.links:
      self.links[self.var['h2']] = []

    row = {}

    # Do magic stuff with this row's data.
    #   One ''row''-entry per row, strange enough.
    for pos, header in self.var['th_data'].items():
      if not pos in self.var['td_data']:
        continue

      td = {}
      if 'title' in self.var['td_attrs'][pos]:
        td['title'] = self.var['td_attrs'][pos]['title'].strip()
      
      if pos in self.var['a_attrs'] and 'href' in self.var['a_attrs'][pos]:
        td['href'] = self.var['a_attrs'][pos]['href'].strip()

      td['text'] = ''.join(self.var['td_data'][pos])
      row[''.join(header)] = td

    if row:
      self.links[self.var['h2']].append(row)

# Get some information using curl

# Run main.
main()



# vim:cc=80:noci:ai:ts=2:et
