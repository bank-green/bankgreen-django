US National Information Center can be downloaded from the US FFIEC:
https://www.ffiec.gov/npw/FinancialReport/DataDownload


python manage.py refresh_datasources usnic

django test datasource.tests.UsnicTestCase

python manage.py dumpdata datasource.Usnic --indent 4 > fixtures/usnic/usnic.json 
python manage.py loaddata fixtures/usnic/usnic.json --app datasource.Usnic

### Random Notes

- CSV_ATTRIBUTES_BRANCHES
    - has unique RSSDs for each branch. It also has a column, `ID_RSSD_HD_OFF` that points to the `#ID_RSSD` of the operating bank in CSV_ATTRIBUTES_ACTIVE
    - STATE_ABBR_NM refers to the state
    - ZIP_CD refers to the zipcode

- CSV_ATTRIBUTES_ACTIVE
    - MJR_OWN_MNRTY refers to ownership by women or minorities. There are text codes here but better to just import as a binary for now. 0 is False

-CSV_RELATIONSHIPS
    - `CTRL_IND` indicates control of a bank by another bank.
        - historic controlling relatinships are indicated. To filter for only active use
            ```
            controlled_all = rels[rels["CTRL_IND"] == 1]
            controlled_all[rels["DT_END"] == 99991231]
            ```
        - banks (offspring) may be controlled by multiple banks (parents).
            - If control is split between multiple parents, use 
                - IF EQUITY_IND == 2, report no parent. (non bank enityt)
                - If Equity_IND == 0, use PCT_OTHER to find controlling commpany
                - IF Equity_IND == 1, use PCT_EQUITY and fallback to PCT_EQUITY_BRACKET'
                                

                - In cases with tied parents, choose any parent with an existing rannking or choose at random.