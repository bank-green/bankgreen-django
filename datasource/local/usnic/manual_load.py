from datasource.models.usnic import *


attr_df = pd.read_csv("./datasource/local/usnic/CSV_ATTRIBUTES_ACTIVE.CSV")
banks = []
num_created = 0
print("USNIC Creating records")
for i, row in attr_df.iterrows():
    try:
        num_created, banks = Usnic._load_or_create_individual_instance(banks, num_created, row)
        print(banks[-1])
    except Exception as e:
        print("\n\n===Usnic failed creation or updating===\n\n")
        print(row)
        print(e)


del attr_df
del banks
print(f"num_created: {num_created}")
del num_created


###############
# BRANCHES
###############

from datasource.models.usnic import *


existing_rssds = [int(x) for x in Usnic.objects.all().values_list("rssd", flat=True)]
branch_df = pd.read_csv(
    "./datasource/local/usnic/CSV_ATTRIBUTES_BRANCHES.CSV",
    usecols=["ID_RSSD_HD_OFF", "CNTRY_NM", "STATE_ABBR_NM"],
)
branch_df = branch_df[branch_df["ID_RSSD_HD_OFF"].isin(existing_rssds)]

print("USNIC updating records with branch information")
for i, row in branch_df.iterrows():
    try:
        Usnic._supplement_with_branch_information(row)
        print(i)
    except Exception as e:
        print("\n\n===Usnic failed to update branch information ===\n\n")
        print(row)
        print(e)

del branch_df


###############
# RELATIONSHIPS
###############

existing_rssds = [int(x) for x in Usnic.objects.all().values_list("rssd", flat=True)]
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
Usnic._add_relationships(rels_df)
