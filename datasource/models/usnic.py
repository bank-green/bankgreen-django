from collections import defaultdict
import re
import threading
from typing import Dict

from django.db import models
from django_countries.fields import CountryField
from django.db.utils import IntegrityError

from brand.models.brand import Brand

from cities_light.models import Country, Region, SubRegion
from jsonfield import JSONField
import pandas as pd
from symspellpy import SymSpell, Verbosity

from datasource.models.datasource import Datasource, SuggestedAssociation
from datasource.pycountry_utils import pycountries

MAX_DICT_EDIT_DISTANCE = 4


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
    """US National Information Center data"""

    rssd = models.CharField(max_length=30, blank=True)
    lei = models.CharField(max_length=30, blank=True)
    cusip = models.CharField(max_length=30, blank=True)
    aba_prim = models.CharField(max_length=30, blank=True)
    fdic_cert = models.CharField(max_length=30, blank=True)
    ncua = models.CharField(max_length=30, blank=True)
    thrift = models.CharField(max_length=30, blank=True)
    thrift_hc = models.CharField(max_length=30, blank=True)
    occ = models.CharField(max_length=30, blank=True)
    ein = models.CharField(max_length=30, blank=True)
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
    control = JSONField(default={})

    def __str__(self):
        return f"{self.name}: {self.pk}: {self.rssd}"

    def __repr__(self):
        return f"<{type(self).__name__}: {self.name}: {self.pk}: {self.rssd}>"

    num_threads = 10

    @classmethod
    def load_and_create(cls, load_from_api=False):

        # load from api or from local disk.
        if not load_from_api:
            print("Loading Usnic data from local copy...")
        else:
            print("No Usnic API. Loading data from local copy...")

        attr_df = pd.read_csv(
            "./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.CSV",
            usecols=[
                "NM_SHORT",
                "NM_LGL",
                "ENTITY_TYPE",
                "URL",
                "#ID_RSSD",
                "ID_LEI",
                "ID_CUSIP",
                "ID_ABA_PRIM",
                "ID_FDIC_CERT",
                "ID_NCUA",
                "ID_THRIFT",
                "ID_THRIFT_HC",
                "ID_OCC",
                "ID_TAX",
                "MJR_OWN_MNRTY",
            ],
        )

        # create instances
        banks = []
        num_created = 0
        print("USNIC Creating records")
        for i, row in attr_df.iterrows():
            try:
                num_created, banks = cls._load_or_create_individual_instance(
                    banks, num_created, row
                )
                print(banks[-1])
            except Exception as e:
                print("\n\n===Usnic failed creation or updating===\n\n")
                print(row)
                print(e)

        del attr_df

        existing_rssds = [int(x) for x in Usnic.objects.all().values_list("rssd", flat=True)]

        # update with branch information
        branch_df = pd.read_csv(
            "./datasource/local/usnic/CSV_ATTRIBUTES_BRANCHES.CSV",
            usecols=["ID_RSSD_HD_OFF", "CNTRY_NM", "STATE_ABBR_NM"],
        )
        branch_df = branch_df[branch_df["ID_RSSD_HD_OFF"].isin(existing_rssds)]
        print("\n\nUSNIC updating records with branch information")
        for i, row in branch_df.iterrows():
            try:
                cls._supplement_with_branch_information(row)
            except Exception as e:
                print("\n\n===Usnic failed to update branch information ===\n\n")
                print(row)
                print(e)

        del branch_df

        # Update with relationship information
        print("\n\nUSNIC records with relationship/control information")
        rels_df = pd.read_csv(
            "./datasource/local/usnic/CSV_RELATIONSHIPS.CSV",
            usecols=[
                "ID_RSSD_OFFSPRING",
                "#ID_RSSD_PARENT",
                "CTRL_IND",
                "DT_END",
                "PCT_EQUITY",
                "PCT_EQUITY_BRACKET",
                "EQUITY_IND",
            ],
        )
        rels_df = rels_df[rels_df["ID_RSSD_OFFSPRING"].isin(existing_rssds)]

        cls._add_relationships(rels_df)

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
            "lei": row.ID_LEI if row.ID_LEI != 0 else None,
            "cusip": row.ID_CUSIP if row.ID_CUSIP != 0 else None,
            "aba_prim": row.ID_ABA_PRIM if row.ID_ABA_PRIM != 0 else None,
            "fdic_cert": row.ID_FDIC_CERT if row.ID_FDIC_CERT != 0 else None,
            "ncua": row.ID_NCUA if row.ID_NCUA != 0 else None,
            "thrift": row.ID_THRIFT if row.ID_THRIFT != 0 else None,
            "thrift_hc": row.ID_THRIFT_HC if row.ID_THRIFT_HC != 0 else None,
            "occ": row.ID_OCC if row.ID_OCC != 0 else None,
            "ein": row.ID_TAX if row.ID_TAX != 0 else None,
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
    def _supplement_with_branch_information(cls, row):

        branch_bank_rssd = row["ID_RSSD_HD_OFF"]

        try:
            bank = Usnic.objects.get(rssd=branch_bank_rssd)
            print(bank)
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
    def _add_relationships(cls, relationship_df):

        threads = []

        # cycle through banks again, this time adding owner relationships
        existing_rssds = [int(x) for x in Usnic.objects.values_list("rssd", flat=True)]

        for child_id in existing_rssds:

            # if "test" in sys.argv:
            if True:
                cls._add_individual_relationship(relationship_df, child_id, existing_rssds)
            else:
                t = threading.Thread(
                    target=cls._add_individual_relationship,
                    args=(relationship_df, child_id, existing_rssds),
                )
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

    @classmethod
    def _add_individual_relationship(cls, relationship_df, child_id, existing_rssds):
        try:
            subset_df = relationship_df[relationship_df["ID_RSSD_OFFSPRING"] == child_id]
            child_bank = Usnic.objects.get(rssd=child_id)
            control_json = child_bank.control
            print(child_bank)

            for i, row in subset_df.iterrows():
                parent_rssd = row["#ID_RSSD_PARENT"]

                parent_usnic_obj = Usnic.objects.filter(rssd=parent_rssd).first()
                parent_name = parent_usnic_obj.name if parent_usnic_obj else "n/a"
                parent_bankgreen_id = parent_usnic_obj.id if parent_usnic_obj else "n/a"

                # if the relationship is not controlling or has ended or parent is not in the dataset
                if (
                    row["CTRL_IND"] != 1
                    or row["DT_END"] != 99991231
                    or parent_rssd not in existing_rssds
                ):
                    continue

                # set equity to exact reported or upper bound if only bracket is available
                pct_equity = 0
                if row["PCT_EQUITY"] != 0:
                    pct_equity = int(row["PCT_EQUITY"])
                elif row["PCT_EQUITY_BRACKET"]:
                    last_pct = row["PCT_EQUITY_BRACKET"].strip().split("-")[-1]
                    pct_equity = int(re.sub(r"[^[0-9\.]", "", last_pct))

                control_json[parent_rssd] = {
                    "equity_owned": pct_equity,
                    "parent_rssd": parent_rssd,
                    "parent_name": parent_name,
                    "parent_bankgreen_id": parent_bankgreen_id,
                }

                if row["EQUITY_IND"] == 1:
                    control_json[parent_rssd]["parent_type"] = "banking"
                elif row["EQUITY_IND"] == 2:
                    control_json[parent_rssd]["parent_type"] = "non-banking"
                elif row["EQUITY_IND"] == 0:
                    control_json[parent_rssd]["parent_type"] = "non-equity-control"

                child_bank.control = control_json
                child_bank.save()
        except Exception as e:
            subset_df = relationship_df[relationship_df["ID_RSSD_OFFSPRING"] == child_id]
            print("\n\n===Usnic failed to update relationship information ===\n\n")
            print(child_id)
            print(subset_df)
            print(e)

    def save(self, *args, **kwargs):
        if self.brand:
            self.update_brand()
        super(Datasource, self).save()

    def update_brand(self) -> None:
        # might need to be run as a celery task?
        # will need a filter for showing what datassources are associated with brands and what are not

        brand = self.brand
        if not brand:  # deal with typing
            return

        if not brand.website_locked:
            brand.website = self.website

        # various identifiers
        if not brand.rssd_locked:
            brand.rssd = self.rssd
        if not brand.lei_locked:
            brand.lei = self.lei
        if not brand.cusip_locked:
            brand.cusip = self.cusip
        if not brand.aba_prim_locked:
            brand.aba_prim = self.aba_prim
        if not brand.fdic_cert_locked:
            brand.fdic_cert = self.fdic_cert
        if not brand.ncua_locked:
            brand.ncua = self.ncua
        if not brand.thrift_locked:
            brand.thrift = self.thrift
        if not brand.thrift_hc_locked:
            brand.thrift_hc = self.thrift_hc
        if not brand.occ_locked:
            brand.occ = self.occ
        if not brand.ein_locked:
            brand.ein = self.ein

        # countries, regions, and subregions are addative
        if self.country not in brand.countries:
            # the temp list is necessary for some queryset weirdness.
            # brand.countries is a list, but can't seem to be appended to
            temp_country_list = [x for x in brand.countries]
            temp_country_list.append(self.country)
            brand.countries = temp_country_list

        new_regions = brand.regions.values_list("id", flat=True) | self.regions.values_list(
            "id", flat=True
        )
        new_regions = new_regions.distinct()
        brand.regions.add(*new_regions)

        new_subregions = brand.subregions.values_list(
            "id", flat=True
        ) | self.subregions.values_list("id", flat=True)
        new_subregions = new_subregions.distinct()
        brand.subregions.add(*new_subregions)

        brand.save()

    @classmethod
    def suggest_associations(cls) -> Dict:
        """Suggest brands for usnic records to be associated to. Writes results to each USNIC.
        returns a dict mapping from usnic to sets of brands, but also links usnic to brands as
        a side effect
        """
        # create dictionaries and spelling corpus
        spelling_dict = Brand.create_spelling_dictionary()
        symspell = SymSpell(max_dictionary_edit_distance=MAX_DICT_EDIT_DISTANCE)
        for word in spelling_dict.keys():
            symspell.create_dictionary_entry(word, 1)

        # collect and record suggestions
        candidate_dict = defaultdict(set)
        usnics = Usnic.objects.all()
        for usnic in usnics:
            suggestions = usnic.search_for_suggested_associations(spelling_dict, symspell)
            for brand_id, certainty in suggestions.items():
                brand = Brand.objects.get(id=brand_id)
                SuggestedAssociation.objects.update_or_create(
                    brand=brand, datasource=usnic, defaults={"certainty": certainty}
                )
                candidate_dict[usnic].add(brand)

        return candidate_dict

    def search_for_suggested_associations(self, spelling_dict, symspell) -> Dict:
        """
        cycles through usnic properties and checks against the spelling dict for exact matches.
        cycles through usnic names and checks against the selling dict for close and exact matches.
        returns a dictionary with {brand_id: match_cetainty}
        """

        id_suggs = [
            self.rssd,
            self.lei,
            self.cusip,
            self.aba_prim,
            self.fdic_cert,
            self.ncua,
            self.thrift,
            self.thrift_hc,
            self.occ,
            self.ein,
        ]
        id_suggs = [spelling_dict.get(x) for x in id_suggs if x and x != ""]
        id_suggs_exact = {x: 0 for x in id_suggs if x}

        # names
        names = [self.name, self.legal_name]
        names = [x for x in names if x and x != ""]

        # exact name matches
        name_suggs_exact = {spelling_dict.get(x): 3 for x in names if spelling_dict.get(x)}

        # misspelling matches
        spelling_suggs = {}
        for name in names:
            edit_distance = min(
                int(len(name) / 5), MAX_DICT_EDIT_DISTANCE
            )  # edit distance increases with word lengh
            matches = symspell.lookup(self.name, Verbosity.CLOSEST, max_edit_distance=edit_distance)
            spelling_suggs = spelling_suggs | {spelling_dict.get(x.term): 8 for x in matches}

        # more certain levels overwrite less certain ones
        return spelling_suggs | name_suggs_exact | id_suggs_exact
