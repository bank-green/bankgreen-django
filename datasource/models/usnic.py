from django.db import models

import pandas as pd
from cities_light.models import Country, Region, SubRegion
from django_countries.fields import CountryField

from datasource.models.datasource import Datasource
from datasource.pycountry_utils import pycountries


class EntityTypes(models.TextChoices):
    AGB = "Agreement Corporation - Banking"
    AGI = "Agreement Corporation - Investment"
    BHC = "Bank Holding Company"
    CPB = "Cooperative Bank"
    DBR = "Domestic Branch of a Domestic Bank"
    DEO = "Domestic Entity Other"
    DPS = "Data Processing Servicer"
    EBR = "Edge Corporation - Domestic Branch"
    EDB = "Edge Corporation - Banking"
    EDI = "Edge Corporation - Investment"
    FBH = "Foreign Banking Organization as a BHC"
    FBK = "Foreign Bank"
    FBO = "Foreign Banking Organization"
    FCU = "Federal Credit Union"
    FEO = "Foreign Entity Other"
    FHD = "Financial Holding Company / BHC (Note: Can be a domestic or foreign-domiciled holding company)"
    FHF = "Financial Holding Company / FBO"
    FNC = "Finance Company"
    FSB = "Federal Savings Bank"
    IBK = "International Bank of a U.S. Depository - Edge or Trust Co."
    IBR = "Foreign Branch of a U.S. Bank"
    IHC = "Intermediate Holding Company"
    IFB = "Insured Federal Branch of an FBO"
    INB = "International Non-bank Subs of Domestic Entities"
    ISB = "Insured State Branch of an FBO"
    MTC = "Non-deposit Trust Company - Member"
    NAT = "National Bank"
    NMB = "Non-member Bank"
    NTC = "Non-deposit Trust Company - Non-member"
    NYI = "New York Investment Company"
    PST = "Non-U.S. Branch managed by a U.S. Branch/Agency of a Foreign Bank for 002’s reporting - Pseudo Twig"
    REP = "Representative Office"
    SAL = "Savings & Loan Association"
    SBD = "Securities Broker / Dealer"
    SCU = "State Credit Union"
    SLHC = "Savings and Loan Holding Company"
    SMB = "State Member Bank"
    SSB = "State Savings Bank"
    TWG = "Non-U.S. Branch managed by a U.S. Branch/Agency of a Foreign Bank - TWIG"
    UFA = "Uninsured Federal Agency of an FBO"
    UFB = "Uninsured Federal Branch of an FBO"
    USA = "Uninsured State Agency of an FBO"
    USB = "Uninsured State Branch of an FBO"
    UNK = "Unknown"


class Usnic(Datasource):
    """ """

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        df = None
        if not load_from_api:
            print("Loading Usnic data from local copy...")
            df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.CSV")
        else:
            print("Loading Usnic data from API...")
            df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.CSV")

        banks = []
        num_created = 0
        for i, row in df.iterrows():
            try:
                num_created, banks = cls._load_or_create_individual_instance(
                    banks, num_created, row
                )
            except Exception as e:
                print("\n\n===Usnic failed creation or updating===\n\n")
                print(row)
                print(e)
        return banks, num_created

    @classmethod
    def _load_or_create_individual_instance(cls, banks, num_created, row):
        source_id = row.NM_SHORT.lower().strip().replace(" ", "_")

        defaults = {
            "name": row.NM_SHORT.strip(),
            "legal_name": row.NM_LGL.strip(),
            "entity_type": row.ENTITY_TYPE
            if row.ENTITY_TYPE.strip() in [x.name for x in EntityTypes]
            else EntityTypes.UNK,
            "country": pycountries.get(row.CNTRY_NM.lower().strip(), None),
            "website": "" if row.URL == "0" else row.URL,
            "rssd": row["#ID_RSSD"],
            "lei": row.ID_LEI if row.ID_LEI is not 0 else None,
            "cusip": row.ID_CUSIP if row.ID_CUSIP is not 0 else None,
            "aba_prim": row.ID_ABA_PRIM if row.ID_ABA_PRIM is not 0 else None,
            "fdic_cert": row.ID_FDIC_CERT if row.ID_FDIC_CERT is not 0 else None,
            "ncua": row.ID_NCUA if row.ID_NCUA is not 0 else None,
            "thrift": row.ID_THRIFT if row.ID_THRIFT is not 0 else None,
            "thrift_hc": row.ID_THRIFT_HC if row.ID_THRIFT_HC is not 0 else None,
            "occ": row.ID_OCC if row.ID_OCC is not 0 else None,
            "ein": row.ID_TAX if row.ID_TAX is not 0 else None,
            "women_or_minority_owned": True if str(row.MJR_OWN_MNRTY) != "0" else False,
        }
        # filter out unnecessary defaults
        defaults = {k: v for k, v in defaults.items() if v == v and v is not None and v != ""}

        bank, created = Usnic.objects.update_or_create(source_id=source_id, defaults=defaults)

        if created:
            bank.save()

        banks.append(bank)
        num_created += 1 if created else 0
        return num_created, banks

    @classmethod
    def supplement_with_branch_information(cls, row):

        branch_bank_rssd = row["ID_RSSD_HD_OFF"]

        try:
            bank = Usnic.objects.get(rssd=branch_bank_rssd)
        except Usnic.DoesNotExist:
            return None

        try:
            country = pycountries.get(row.CNTRY_NM.lower().strip(), (None,))
            country = Country.objects.get(code2=country)
        except Country.DoesNotExist:
            return bank

        try:
            state = Region.objects.get(
                geoname_code=row.STATE_ABBR_NM.upper().strip(), country=country
            )
            bank.regions.add(state)
        except Region.DoesNotExist or Region.MultipleObjectsReturned:
            pass

        # some potential to do subregions but will need to translate from PLACE_CD PHYSICAL PLACE CODE to geocode

        bank.save()
        return bank

    @classmethod
    def add_relationships(cls, relationship_df):
        # cycle through banks again, this time adding owner relationships
        df = pd.read_csv("./datasource/local/usnic/CSV_RELATIONSHIPS.CSV")
        existing_rssds = [x for x in Usnic.objects.values_list("rssd", flat=True)]

        for existing_rssd in existing_rssds:
            subset_df = df[df["ID_RSSD_OFFSPRING"] == existing_rssd]

            for i, row in df.iterrows():
                child_id = row["ID_RSSD_OFFSPRING"]
                parent_id = row["#ID_RSSD_PARENT"]

                # if the relationship has ended or either the parent/offspring is not in the dataset
                if row["DT_END"] != 99991231 or parent_id not in existing_rssds or child_id not in existing_rssds:
                    continue 




        # for i, row in df.iterrows():

            
        #     try:
        #         child = Usnic.objects.get(rssd=str(row["ID_RSSD_OFFSPRING"]))
        #         parent = Usnic.objects.get(rssd=str(row["#ID_RSSD_PARENT"]))
        #     except Usnic.DoesNotExist:
        #         continue


            # if not child.subsidiary_of_1 or child.subsidiary_of_1 != parent:
            #     # child.subsidiary_of_1 = Usnic.objects.get(rssd=str(row['#ID_RSSD_PARENT']))
            #     child.subsidiary_of_1 = parent
            #     child.subsidiary_of_1_pct = row["PCT_EQUITY"]
            # elif not child.subsidiary_of_2 or child.subsidiary_of_2 != parent:
            #     child.subsidiary_of_2 = parent
            #     child.subsidiary_of_2_pct = row["PCT_EQUITY"]
            # elif not child.subsidiary_of_3 or child.subsidiary_of_3 != parent:
            #     child.subsidiary_of_3 = parent
            #     child.subsidiary_of_3_pct = row["PCT_EQUITY"]
            # elif not child.subsidiary_of_4 or child.subsidiary_of_4 != parent:
            #     child.subsidiary_of_4 = parent
            #     child.subsidiary_of_4_pct = row["PCT_EQUITY"]
            # else:
            #     pass
            # child.save()

    rssd = models.CharField(max_length=15, blank=True)
    lei = models.CharField(max_length=15, blank=True)
    cusip = models.CharField(max_length=15, blank=True)
    aba_prim = models.CharField(max_length=15, blank=True)
    fdic_cert = models.CharField(max_length=15, blank=True)
    ncua = models.CharField(max_length=15, blank=True)
    thrift = models.CharField(max_length=15, blank=True)
    thrift_hc = models.CharField(max_length=15, blank=True)
    occ = models.CharField(max_length=15, blank=True)
    ein = models.CharField(max_length=15, blank=True)
    website = models.URLField(
        "Website of this brand/data source. i.e. bankofamerica.com", null=True, blank=True
    )

    legal_name = models.CharField(max_length=200, null=False, blank=True)
    entity_type = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        choices=EntityTypes.choices,
        default=EntityTypes.UNK,
    )

    country = CountryField(multiple=False, help_text="Country the bank is locatd in", blank=True)  # type: ignore
    regions = models.ManyToManyField(
        Region, blank=True, help_text="regions in which there are local branches of a bank"
    )
    subregions = models.ManyToManyField(
        SubRegion, blank=True, help_text="regions in which there are local branches of a bank"
    )

    women_or_minority_owned = models.BooleanField(default=False)
