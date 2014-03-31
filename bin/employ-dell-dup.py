#!/usr/bin/python2

import urllib2 # Deprecated
from optparse import OptionParser # Deprecated
import tempfile
import os
import shutil
import re
import sys
import subprocess

def main():
  optparse=OptionParser(
    description="Download and install Dell DUP files (or whatever)"
  )

  optparse.add_option("-s", "--silent", default=False, action="store_true")
  optparse.add_option("-v", "--verbose", default=False, action="store_true")
  optparse.add_option("-U", "--url", default=None)
  optparse.add_option("-W", "--workdir", default=None)
  optparse.add_option("-1", "--one", default=False, action="store_true")
  optparse.add_option("-o", "--option", default=[], action="append")
  optparse.add_option("-k", "--keep-downloads", default=False, action="store_true")
  optparse.add_option("-d", "--force-download", default=False, action="store_true")
  optparse.add_option("-X", "--exclude", default=None)
  optparse.add_option("-F", "--pattern", default=None)
  optparse.add_option("-i", "--ignorecase", default=False, action="store_true")
  (opt, args) = optparse.parse_args()

  mess = {}

  xopt = {}
  for x in opt.option:
    x = x.split('=',1)
    if len(x) == 2:
      xopt[x[0]] = x[1]
      continue
    if x.startswith('!'):
      xopt[x[1:]] = False
    else:
      xopt[x] = True
  
  if opt.ignorecase:
    xopt['reopt'] = re.IGNORECASE
  else:
    xopt['reopt'] = 0

  if opt.pattern:
    opt.pattern = re.compile(opt.pattern, xopt['reopt'])

  if opt.exclude:
    opt.exclude = re.compile(opt.exclude, xopt['reopt'])


  # If no opt.workdir is specified, create a tmpdir.
  tmpdir = None
  if not opt.workdir:
    if opt.verbose:
      msg("Create temporary directory")
    
      if not opt.silent and opt.keep_downloads:
        msg("Warning: --keep-downloads \"crashes\" with not specifying --workdir.",
          "Oh well. I'll go ahead and delete the stuff.")
    tmpdir = tempfile.mkdtemp()
    if opt.verbose:
      msg("Temporary directory created: %s" %(tmpdir))
    opt.workdir = tmpdir
    mess['tmpdir'] = tmpdir
  else:
    if not os.path.isdir(opt.workdir):
      msg("No such directory: %s" (opt.workdir))
      sys.exit(1)

    if opt.verbose:
      msg("Use workdir: %s" %(opt.workdir))
 
  # EmployList!
  employlist = EmployList(opt, xopt)
 

  # Read URL/file
  if not opt.url:
    msg("No url specified. I've got nothing to do!")
    cleanup(mess,opt,xopt)
    sys.exit(1)

  # Read url
  try:
    if not employlist.read_url(opt.url):
      cleanup(mess, opt, xopt)
      sys.exit(1)
  except IOError, e:
    msg(e)
    cleanup(mess, opt, xopt)
    sys.exit(1)

    downloaded = employlist.fetch()
  employlist.employ()


 
#
#    if not opt.keep_downloads:
#      for details in downloads:
#        del_download(details, opt, xopt)
#        #cleanup(mess, opt, xopt)
#        #ys.exit(1)
# 
#
  # Cleanup
  cleanup(mess,opt,xopt)

def msg(x, *y):
  print "*** %s" %(x)
  for line in y:
    print "    %s" %(line)

def cleanup(mess,opt,xopt):
  # If tmpdir was created, cleanup.
  if 'tmpdir' in mess:
    if opt.verbose:
      msg("Delete temporary directory (and content): %s" %(mess['tmpdir']))
    shutil.rmtree(mess['tmpdir'])    

class EmployList:
  def __init__(self, opt, xopt):
    self.opt = opt
    self.xopt = xopt
    self.files = {}
  
  def read_url(self, url):
    filelist = []
    if bool(re.search(r'://', url)):
      if self.opt.verbose:
        msg("Fetch filelist from URL: %s" %(url))
      filelist = urllib2.urlopen(url).read()
    else:
      if self.opt.verbose:
        msg("Fetch filelist from local file: %s" %(url))
      filelist = open(url, 'r').read()

    # If xopt has prefix, use that as prefix rather than url
    if 'prefix' in self.xopt:
      url_prefix = self.xopt['prefix']
    else:
      url_prefix = url.rsplit('/', 1)[0]

    # Filter filelist. :)
    filelist = filter(lambda a: not bool(re.match("^(#.*|\s*)$", a)), filelist.split("\n"))
    
    for file in filelist:
      source = os.path.join(url_prefix, file)
      target = os.path.join(self.opt.workdir, file)
      
      isfile = os.path.isfile(target)

      if self.opt.force_download or not isfile:
        fetch = True
      else: 
        fetch = False

      self.files[file] = {
        'file': file,
	'source': source,
        'target': target,
        'fetch': fetch,
        'isfile': isfile,
        'employed': False,
        'fetch_successful': False
      }

    return True

  def fetch(self, limit = None):
    counter = 0
    downloaded = {}
    for file,details in self.files.items():
      if not details['fetch']:
        continue

      counter += 1

      if limit and limit < counter:
        return downloaded

      if not self.opt.silent:
        msg("Fetch %s from %s" %(details['target'], details['source']))
      
      this = self.curl(details)    
      if this:
        downloaded[file] = this
      else:
        return downloaded
    return downloaded


  def curl(self, details):
    curl = 'curl'
    curlopt = ['--show-error', '--location', '--remote-time']
    if self.opt.silent:
      curlopt += ["--silent"]
    curlopt += ['--output', os.path.join(self.opt.workdir, details['target']), details['source']]
    try:
      exco = subprocess.call([curl] + curlopt)
    except KeyboardInterrupt:
      msg("KeyboardInterrupt")
      return False

    if exco != 0:
      msg("curl failed")
      return False

    details['fetch_successful'] = True
    details['fetch'] = False
    details['isfile'] = os.path.isfile(details['target'])
    return details

  def employ(self, downloads = None):
    if downloads == None:
      downloads = self.files

    for file, details in downloads.items():
      if self.opt.pattern and not self.opt.pattern.match(details['file']):
        continue

      if self.opt.exclude and self.opt.exclude.match(details['file']):
        continue

      if not details['isfile']:
        msg("Will not employ %s: DUP is not ''detected'' as file" %(details['file']))
        return
      if not self.opt.silent:
        msg("Employing: %s" % details['file'])
      
      sh =  ['sh', details['target'], '-n', '-q']
      try:
        exco = subprocess.call(sh)
      except KeyboardInterrupt:
        msg("KeyboardInterrupt")
        raise KeyboardInterrupt
      
      details['employed'] = True
      details['employ_exco'] = exco
    return

  def cleanup(self, files = None):
    if self.keep_downloads:
      return True
     
    if not files:
      files = list.files

    for file, details in files.items():
      if os.path.isfile(details['target']):
        if self.opt.verbose:
          msg("Delete download: %s" %(details['target']))
        os.remove(details['target'])
  
main()

# vim: ts=2:et:ai:nocp
