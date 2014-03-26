===============
PE-C fw scraper
===============

Background
----------
[poweredgec.com](http://www.poweredgec.com) provides some good tools for 
sysadmins who happen to run Dell systems, and especially Dell's C-class.. One
of those tools is a scraper that well, scrapes [support.dell.com](http://support.dell.com) 
for firmwares.

I want to use that scraper to keep my metal polished and up to date. 

Scripts
-------

  * bin/pe_fw_scraper.py
    * Does the actual scraping of the scraper.
      * By default: www.poweredgec.com/latest_PE-C_fw.html
    * Creates a JSON file with information from the scraper.
      * Possibly based on hardware class.
    * Updates filesize and modification date based on 
      HTTP headers from Dell.com
    * (May) download firmwares
      * Based on a filename pattern.
    * Creates a list of ''latest'' firmwares.
      
  * bin/pe_fw_info.py
    * Shows information about the JSON file from the fw scraper.

pe_fw_scraper.py
----------------
```
Usage: pe_fw_scraper.py [options]

Scrape the scraper!

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         
  -S, --silent          
  -J JSON, --json=JSON  JSON File (Env: PE_FW_JSON)
  -U URL, --url=URL     Scraper URL (Env: PE_FW_SCRAPER). May be a local file.
  -L LATEST, --latest=LATEST
                        Update file LATEST with latest firmwares (Env:
                        PE_FW_LATEST)
  -P PREFIX, --latest-prefix=PREFIX
                        Prefix lines of LATEST file with PREFIX (Env:
                        PE_FW_LATEST_PREFIX)
  -C CACHE, --cache=CACHE
                        Target directory for downloads
  -H HW, --hw=HW        Hardware class to fetch firmwares for
  -F PATTERN, --pattern=PATTERN
                        Filename pattern
  -X EXCLUDE, --exclude=EXCLUDE
                        Exclude filenames matching
  -i, --ignorecase      Ignore case when matching regexes
  --no-header-info      
  --no-save-json        
  --retry-unknown-size  
  --no-download         
  -D DUMP, --dump=DUMP  
```

Scrape the scraper! 
-------------------

```
./pe_fw_scraper.py \
  -v  \
  --url=latest_PE-C_fw.html \ 
  --json=fw_scraper.json  \
  --latest-prefix=cache/ \
  --latest=LATEST \
```
Download some bin files:

  ./pe_fw_scraper.py -v --json=fw_scraper.json --cache=cache --latest=cache/LATEST_BIN -i --pattern bin
