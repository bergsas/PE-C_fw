===============
PE-C fw scraper
===============

Scrape the scraper! 
-------------------

  `./pe_fw_scraper.py 
    -v 
    --url=latest_PE-C_fw.html 
    --json=fw_scraper.json  
    --latest-prefix=cache/ 
    --latest=LATEST`

Download some bin files:

  ./pe_fw_scraper.py -v --json=fw_scraper.json --cache=cache --latest=cache/LATEST_BIN -i --pattern bin
