#!/usr/bin/python2

import urllib2 # Deprecated? Oh well.
import sgmllib # Deprecated? Yes sir!
from optparse import OptionParser # Deprecated you say? Who cares?!
import json
import os
import re
import subprocess

def main():
  # Argument parsing
  optparse = OptionParser(
    description="Scrape Dell driver pages",
    epilog="Probably one of a thousands other scrapers"
  )
  optparse.add_option("-s", "--silent", action="store_true", default=False)
  optparse.add_option("-v", "--verbose", action="store_true", default=False)
  optparse.add_option("-A", "--auto", default=None)
  optparse.add_option("-J", "--json", default=None)
  optparse.add_option("-U", "--url", default=None)
  optparse.add_option("-C", "--cache", default=None)
  optparse.add_option("-d", "--download", action="store_true", default=False)
  optparse.add_option("-L", "--latest", default=None)
  optparse.add_option("-P", "--latest-prefix", default="")
  optparse.add_option("-M", "--match", default="FileName")
  optparse.add_option("-F", "--pattern", default=None)
  optparse.add_option("-X", "--exclude", default=None)
  optparse.add_option("-o", "--option", action="append", default=[])

  optparse.add_option("-i", "--ignorecase", action="store_true", default=False)
  optparse.add_option("-D", dest="dump", action="append", default=[])
  (opt, args) = optparse.parse_args()

  # Fix the dump list. 
  known_dumpers = ('driversdata', 'groups', 'driverdetails', 'filedetails')

  # Allow for all kinds of options from command line. Hurrah!
  xopt = {} 
  for o in opt.option:
    o = o.split('=',1)
    if len(o) == 2:
      if o[0] in xopt and isinstance(list, xopt[o[0]]):
        xopt[o[0]] += [o[1]]
      else:
        xopt[o[0]] = o[1]
      continue

    if o.startswith('!'):
      xopt[o[1:]] = False
    else:
      xopt[o] = True

  for i,n in enumerate(opt.dump):
    opt.dump[i] = n.lower()
    if not opt.dump[i] in known_dumpers:
      msg("Unknown dumpers: %s"%(opt.dump[i]), "Known dumpers: %s"%(" ".join(known_dumpers)))
      exit(1)
  # Ignore case in regular expressions
  regex_opt = 0
  if opt.ignorecase:
    regex_opt += re.IGNORECASE

  # Compile a few patterns, if necessary.
  if opt.pattern:
    pattern = re.compile(opt.pattern, regex_opt)
  else:
    pattern = None

  if opt.exclude:
    exclude = re.compile(opt.exclude, regex_opt)
  else:
    exclude = None

  # Compile expression for args, if any.
  if args:
    expression = makeexpression(args, regex_opt)
    if not expression:
      msg ("Failed to compile expression from: %s" %(" ".join(args)))
      exit(1)
  else:
    expression = None

  url = opt.url
  
  if opt.auto:
    url = autourl(opt.auto)

  if not url:
    msg ("No url/file specified. I got nothing to do!")
    exit(1)
  
  # Open file/url:
  parser = downloads_driversdata() 
  
  # If opt.url matches ://, open as URL
  if bool(re.search(r"://", url)):
    urlopen = urllib2.urlopen(url)

  # Else: Open as file.
  else:
    urlopen = open(url, 'r')

  html = urlopen.read()
  
  if 'savehtml' in xopt:
    with open(xopt['savehtml'], 'w') as htmlfile:
      htmlfile.write(html)
  
  parser.feed(html)

  # Driversdata is stored here:
  driversdata = parser.driversdata

  # If you want to dump the driversdata JSON, do it here.
  if 'driversdata' in opt.dump:
    print json.dumps(parser.driversdata, indent=2)
    exit(0)

  # Create my own little representation of the driversdata stuff
  groups = regroup_driversdata(driversdata)

  # Dump groups.
  if 'groups' in opt.dump:
    print json.dumps(groups, indent=2)
    exit(0)
  
  download = []
  latest = []

  # Go trhough files and do stuff
  for group, drivers in groups.items():
    for driverid, driverdetails in drivers.items():
      driverdetails['group'] = group
      if 'driverdetails' in opt.dump:
        msg ("driverdetails for %s" %(driverid))
        print json.dumps(driverdetails, indent=2)

      for fileid, filedetails in driverdetails['files'].items():
        # filedetails['FileSize']
        # If pattern is specified and file doens't match, 
        #   move on
       
        for key in driverdetails.keys():
          if key == 'files':
            continue
          filedetails[key] = driverdetails[key]
        

        try:
          if pattern and not pattern.search(filedetails[opt.match]):
            continue

          # If exclude is enabled and this file matches, go on.
          if exclude and exclude.search(filedetails[opt.match]):
            continue

          if expression and not matchexpression(expression, filedetails):
            break
        
        except KeyError as e:
          print "Unknown key: %s"% (e)
          exit(1)

        if 'filedetails' in opt.dump:
          msg("filedetails for %s" %(fileid))
          print json.dumps(filedetails, indent=2)
          continue

        # os.path.getsize(join)
        # os.path.join(opt.cache, filename)
        # os.path.isfile(join):
 
        
        filesize, filename, href = filedetails["FileSize"], filedetails["FileName"], filedetails["DellHttpFileLocation"]
        
        if opt.cache:
          cachedfile = os.path.join(opt.cache, filename)

          if not os.path.isfile(cachedfile) or os.path.getsize(cachedfile) != int(filesize):
            download += [[cachedfile, filename, href]] 

        if opt.latest and filename:
          latest += [filename]

        if not opt.silent:
          print "%s" %(href)

  # At this point we may have two jobs to do: make the 'latest' file
  #   and download some files.

  if opt.latest: 
    with open(opt.latest, 'w') as latest_file:
      for line in latest:
        latest_file.write("%s%s\n" %(opt.latest_prefix, line))

  if opt.download and opt.cache:
    try:
      for down in download:
        down += [opt]
        curl_download(*down)
    except KeyboardInterrupt:
      exit(1)

# Parse HTML that looks like http://www.dell.com/support/home/us/en/04/product-support/product/poweredge-c6220-2/drivers
# Look for hidden input with id ''driversdata'': Its 'value' attribute seems to
# be a JSON! Hurra.

class downloads_driversdata(sgmllib.SGMLParser):
  def __init__(self, verbose=0):
    sgmllib.SGMLParser.__init__(self, verbose)
    self.driversdata = {}

  def start_input(self, attrs):
    # Convert attrs tuple to dict.
    attrs = dict((x,y) for x,y in attrs)
    if not 'id' in attrs or attrs['id'] != 'driversdata' or not 'value' in attrs:
      return
    self.driversdata = json.loads(attrs['value'])

# Regroup the driversdata stuff. To make it funnier!
def regroup_driversdata(driversdata):
  if not 'GroupItem' in driversdata:
    print "JSON not as expected. I'll die now."
    exit(1)

  # Groups
  groups = {}
  for groupdata in driversdata['GroupItem']:
    # groupdata = [u'GroupItemName', u'groupItemId', u'Drivers', u'groupItem', u'groupItemToolTip']
    # We need the attrs GroupItemName and Drivers:
    if not ('GroupItemName' in groupdata and 'Drivers' in groupdata):
      continue

    group = groups[groupdata['GroupItemName']] = {}

    # Flatten this stuff out a bit.
    for driver in groupdata['Drivers']:
      # driver = [u'IsSecure', u'DriverId', u'Imp', u'SystemId', u'DriverName', 
      #   u'IsRestart', u'Type', u'ImpId', u'IsCReqExst', u'ReleaseDate', 
      #   u'TypeName', u'Day', u'Minute', u'ProductCode', u'BrfDesc', 
      #   u'CtgKey', u'FileFrmtInfo', u'Hour', u'AppOses', u'Cat', 
      #   u'DellVer', u'IsRestricted', u'AppFileFrmts', u'IsPReqExst', 
      #   u'PReqs', u'VendorVer', u'AppLngs', u'LUPDDate', u'Month', 
      #   u'CReqs', u'Second', u'Year', u'IsOthVerExst', u'OthFileFrmts']

      this = {}

      # Some interesting attributes (metadata, as it happens):
      for attr in ('DriverId', 'DriverName', 'Cat', 'TypeName', 'Imp', 
        'ReleaseDate', 'DellVer', 'LUPDDate'):
        if attr in driver:
          this[attr] = driver[attr]
        else:
          this[attr] = None

      files = this['files'] = {}

      #print json.dumps(this, indent=2)

      # Useless entry if it's without these attributes:
      if not ('FileFrmtInfo' in driver and 'FileId' in driver['FileFrmtInfo']):
        continue

      # I **hope** the 'FileId' attribute is unique and "safe".
      files[driver['FileFrmtInfo']['FileId']] = driver['FileFrmtInfo']
      
      # [u'DriverId', u'FileFormatName', u'HttpFileLocation', 
      #   u'FtpFileLocation', u'ProductCode', u'Sha1', u'IsMoreFormatsExists', 
      #   u'Md5Hash', u'IsOtherVersionExists', u'FileCreationTime', 
      #   u'DellHttpFileLocation', u'IsDownloadAndInstall', 
      #   u'FileTypeDescription', u'CategoryId', u'CategoryName', 
      #   u'DownloadType', u'FileTypeCode', u'FileFormatDescription', 
      #   u'FileFormatId', u'FileName', u'FileFormatCode', u'FileSize', 
      #   u'FileId']

      # Add a file to files
      for other in driver['OthFileFrmts']:
        # Will probably overwrite dict item from above. Oh well.
        files[other['FileId']] = other
         
      # Add group driver to this group
      group[this['DriverId']] = this
    
  # Return from function
  return groups 

# autourl. Well. Generate autourl.
def autourl(stuff):
# This *may* work:
  by_tag = "http://www.dell.com/support/home/us/en/04/product-support/servicetag/%s/drivers"
  
  if not bool(re.search(r"=", stuff)):
    return by_tag %(stuff)

# Create a simple expression using a list of strings
#   Hack hack hack!
def makeexpression(arg, regex_opt):
  result = []
  comp = re.compile(r"^([^=!]+)([=!]+)(.*)$")
  for this in arg:
    split = comp.match(this)

    # If this doesn't match, return None.
    if not bool(split):
      return None
    operator = split.group(2)

    # Known 'operators':
    #   =, == and !=
    if operator == '==':
      operator = '='

    if not (operator == '=' or operator == '!='):
      return None

    # COmpile expression
    compiled = re.compile(split.group(3), regex_opt)

    result += [[split.group(1), operator, compiled]]
  return result

# expression = [
#   [field, operator, compiled_regex], ...
# ]
#
def matchexpression(expression, details):
  for expr in expression:
    # If "operator" is match (=): and details[FIELD]
    #   doesn't match, return False
    if expr[1] == '=' and not expr[2].search(details[expr[0]]):
      return False
      
    # If operator is not match (!=), and field matches return False
    if expr[1] == '!=' and expr[2].search(details[expr[0]]):
      return False
  return True

# I gotta learn python. :)                                                      
# In ruby I'd do something like:                                                
#  arr = arr + arr                                                              
def curl_download(outfile, filename,  href, opt):                                
  if not opt.silent:                                                            
    msg("Try and download %s from %s" %(filename, href))                        
  curl='curl'                                                                   
  curl_options = ['--location', '--remote-time']                                                 
  if opt.silent:                                                                
    curl_options += ['--silent', '--show-error']
  return subprocess.call([curl]+curl_options+["--output", outfile, href])       

# msg                                        
# Output messages in a "standardized format".
def msg(first, *x):                          
  print "*** %s" %(first)                    
  for line in x:                             
    print "    %s" %(line)                   



# Run main
main()

# vim:cc=80:noci:ai:ts=2:et 
