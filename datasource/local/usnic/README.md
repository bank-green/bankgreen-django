US National Information Center can be downloaded from the US FFIEC:
https://www.ffiec.gov/npw/FinancialReport/DataDownload


python manage.py refresh_datasources usnic

django test datasource.tests.UsnicTestCase


### Random Notes

- CSV_ATTRIBUTES_BRANCHES
    - has unique RSSDs for each branch. It also has a column, `ID_RSSD_HD_OFF` that points to the `#ID_RSSD` of the operating bank in CSV_ATTRIBUTES_ACTIVE
    - STATE_ABBR_NM refers to the state
    - ZIP_CD refers to the zipcode

- CSV_ATTRIBUTES_ACTIVE
    - MJR_OWN_MNRTY refers to ownership by women or minorities. There are text codes here but better to just import as a binary for now. 0 is False
