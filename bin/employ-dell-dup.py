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

  # Read URL/file
  if not opt.url:
    msg("No url specified. I've got nothing to do!")
    cleanup(mess,opt,xopt)
    sys.exit(1)

  filelist_raw = None
  try: 
    if bool(re.search(r'://', opt.url)):
      if opt.verbose:
        msg("Fetch filelist from URL: %s" %(opt.url))
      filelist_raw = urllib2.urlopen(opt.url).read()
    else:
      if opt.verbose:
        msg("Fetch filelist from local file: %s" %(opt.url))
      filelist_raw = open(opt.url, 'r').read()
  except IOError, e:
    msg(e)
    cleanup(mess,opt,xopt)
    sys.exit(1)
  
  # If xopt has prefix, use that as prefix rather than url
  if 'prefix' in xopt:
    prefix = xopt['prefix']
  else:
    prefix = opt.url.rsplit('/', 1)[0]

  # Filter filelist. :)
  filelist = filter(lambda a: not bool(re.match("^(#.*|\s*)$", a)), 
    filelist_raw.split("\n"))

  # Create list of ... source files and target files.
  downloads = []
  for file in filelist:
    filename = file.rsplit('/', 1)

    if len(filename) == 1:
      filename=filename[0]
    else:
      filename=filename[1]
    downloads += [{'url': "%s/%s" % (prefix, file), 'filename': filename}]

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
 
  # Either we download all and then do magic stuff (i.e. emply 
  #  them, or we do one and one).

  no = 0
  totnum = len(downloads)
  
  # Do one at the time:
  if opt.one:
    #
    for details in downloads:
      if not download(details, opt, xopt, no, totnum):
        cleanup(mess, opt, xopt)
        sys.exit(1)
        # Ugh. Download may have failed
	continue

      if not employ(details, opt, xopt, no, totnum):
        # Ugh, employ may have failed
	continue

      if not opt.keep_downloads:
        del_download(details, opt, xopt)
        #  cleanup(mess, opt, xopt)
        #	sys.exit(1)
  else:
    # DOwnload them all
    for details in downloads:
      if not download(details, opt, xopt, no, totnum):
        cleanup(mess, opt, xopt)
	sys.exit(1)
        # Download failed
	continue

    # Employ them all
    for details in downloads:
      if not employ(details, opt, xopt, no, totnum):
        # Emply may have failed
	continue

    # Delete them all
    if not opt.keep_downloads:
      for details in downloads:
        del_download(details, opt, xopt)
        #cleanup(mess, opt, xopt)
        #ys.exit(1)
 

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

def del_download(details, opt, xopt):
  rmfile = os.path.join(opt.workdir, details['filename'])

  if opt.verbose:
    msg("Delete download: %s" %(rmfile))
  os.remove(rmfile)
#  return os.remove(rmfile)

def download(details, opt, xopt, no, totnum):
  curl = 'curl'
  curlopt = ['--show-error', '--location']
  if opt.silent:
    curlopt += ["--silent"]
  curlopt += ['--output', os.path.join(opt.workdir, details['filename']), details['url']]
  
  if not opt.silent:
    msg("[%d/%d]: Fetch %s from %s" %(no, totnum, details['filename'], details['url']))

  try:
    exco = subprocess.call([curl] + curlopt)
  except KeyboardInterrupt:
    msg("KeyboardInterrupt")
    return False

  if exco != 0:
    msg("curl failed")
    return False

  return True

def employ(details, opt, xopt, no, totnum):
  print "employ"
  return True
main()

# vim: ts=2:et:ai:nocp
