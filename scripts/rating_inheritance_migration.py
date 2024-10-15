# This is a script that was made to run from python manage.py shell
# the purpose is to set rating inheritance on banks, migrating data from the old airtable.
# it's here for archival purposes.

from brand.models import *


not_found = []
undone = []


def inherit(input, subsidiary_obj, parent_obj):
    if int(input) == 1 and subsidiary_obj and parent_obj:
        subsidiary_obj.commentary.inherit_brand_rating = parent_obj
        subsidiary_obj.commentary.save()
        print(f"{subsidiary_obj} updated")
    else:
        print(f"not updated")


def find(sub, par):
    subsidiary_obj, parent_obj = None, None
    try:
        subsidiary_obj = Brand.objects.get(tag=sub)
    except Brand.DoesNotExist:
        print(f"subsidiary {sub} doesn't exist")
        not_found.append((sub, par))
        return
    try:
        parent_obj = Brand.objects.get(tag=par)
    except Brand.DoesNotExist:
        print(f"parent {par} doesn't exist")
        not_found.append((sub, par))
        return
    print(f"sub rating: {subsidiary_obj.commentary.rating} : {sub}")
    print(f"par rating: {parent_obj.commentary.rating} : {par}")
    if (
        subsidiary_obj.commentary.rating == parent_obj.commentary.rating
        and subsidiary_obj != parent_obj
    ):
        inherit(1, subsidiary_obj, parent_obj)
    else:
        # undone.append((sub, par,))
        print("1 to inherit")
        print("2 to cancel")
        decision = input()
        inherit(decision, subsidiary_obj, parent_obj)


find("garantibank", "bilbao_vizcaya_argentaria_bank")

find("banque_populaire", "bpce_group")
find("bank_gospodarki_ywno_ciowej", "bnp_paribas")
find("abbey_national_santander", "santander")
find("alliance__leicester_santander", "santander")
find("clydesdale_bank_virgin_money", "virgin_money")
find("carter_allen_santander", "santander")
find("coutts_rbs", "natwest")
find("ms_bank_hsbc", "hsbc")
find("john_lewis_partnership_card_hsbc", "hsbc")
find("first_direct_hsbc", "hsbc")
find("intelligent_finance_lloyds_banking", "lloyds_banking_group_plc")
find("hbos__bank_of_scotland_lloyds", "lloyds_banking_group_plc")
find("first_national_santander", "santander")
find("tsb_banco_sabadell", "banco_sabadell")
find("ulster_bank_rbs", "natwest")
find("yorkshire_bank_virgin_money", "virgin_money")
find("bank_austria", "unicredit")
find("ubank", "national_australia_bank_group")
find("handelsbanken", "handelsbanken")
find("banksa", "westpac")
find("bank_of_scotland", "lloyds_banking_group_plc")
find("bank_of_melbourne", "commonwealth_bank")
find("john_lewis_finance", "hsbc")
find("rams", "westpac")
find("st_george_bank", "westpac")
find("rbs", "natwest")
find("bankwest", "commonwealth_bank")
find("bnp_paribas_fortis", "bnp_paribas")
find("morgan_stanley", "mitsubishi_ufj_fncl_grp")
find("bank_of_china", "central_huijin_inv")
find("cibc", "canadian_imperial_hold")
find("santander", "santander")
find("natixis", "bcpe_group")
find("suntrust_bank", "truist")
find("natwest", "natwest")
find("bbva_bancomer", "bbva")
find("bank_of_the_west", "bnp_paribas")
find("postbank", "deutsche_bank")
find("fidor_bank_ag", "bpce_group")
find("ukrsotsbank", "unicredit")
find("anz_fiji", "australia_and_new_zealand_banking_group")
find("stgeorge_bank", "westpac")
find("industrial_and_commercial_bank_of_china_asia", "industrial_commercial_bank_of_china")
find("the_hongkong_and_shanghai_banking_corporation_limited", "hsbc")
find("hsbc_turkey", "the_hongkong_and_shanghai_banking_corporation_limited")
find("hang_seng_bank", "the_hongkong_and_shanghai_banking_corporation_limited")
find("absa_bank_uganda_limited", "absa_bank_limited")


find("standard_chartered_taiwan", "standard_chartered")
find("citizens_financial_group", "rbs")
find("nordea_bank_russia", "nordea")
find("nordea_direct", "nordea")
find("nordea_bank_polska", "nordea")
find("vseobecna_uverova_banka", "intesa_sanpaolo")
find("intesa_sanpaolo_bank_albania", "intesa_sanpaolo")
find("simple", "bilbao_vizcaya_argentaria_bank")
find("bbva_colombia", "bilbao_vizcaya_argentaria_bank")
find("suntrust_banks", "suntrust_bank")
find("denizbank", "sberbank_of_russia")
find("rbc_bank", "royal_bank_of_canada")

find("bmo_harris_bank", "bmo_financial_group")
find("brd__society_general_group", "societe_generale")

find("credit_du_nord", "societe_generale")
find("komercni_banka", "societe_generale")
find("uib", "societe_generale")

find("banque_francaise_commerciale_ocean_indien", "societe_generale")
find("marseillaise_credit_company", "credit_du_nord")
find("italian_national_labor_bank", "bnp_paribas")
find("bgl_bnp_paribas", "bnp_paribas")
find("union_bancaire_pour_le_commerce_et_lindustrie", "bnp_paribas")
find("credit_lyonnais", "credit_agricole_group")
find("credit_agricole_nord_de_france", "credit_agricole_group")
find("french_industrial_and_commercial_bank", "credit_mutuel")
find("monabanq", "credit_mutuel")
find("banque_cic_ouest", "french_industrial_and_commercial_bank")
find("banque_scalbertdupont", "french_industrial_and_commercial_bank")
find("groupe_caisse_depargne", "bpce_group")
find("banque_palatine", "bpce_group")
find("credit_foncier_de_france", "bpce_group")
find("ing_bank_slaski", "ing_group")
find("halifax", "lloyds_banking_group_plc")
find("ceskoslovenska_obchodna_banka", "kbc")
find("kh_bank", "kbc")
find("hsbc_uk", "hsbc")
find("ms_bank", "hsbc_uk")
find("hsbc_bank_china", "the_hongkong_and_shanghai_banking_corporation_limited")
find("cassa_commerciale_australia", "bendigo_bank")
find("cassa_commerciale_australia", "bendigo_bank")
find("banco_de_chile", "citi")
find("comdirect", "commerzbank")
find("komercni_banka", "societe_generale")
find("csob", "kbc")
find("ceska_sporitelna", "erste_group_bank_ag")
find("mbank", "commerzbank")


# remaining
find("banque_francaise_commerciale_ocean_indien", "societe_generale")
find("marseillaise_credit_company", "credit_du_nord")
find("italian_national_labor_bank", "bnp_paribas")
find("bgl_bnp_paribas", "bnp_paribas")
find("union_bancaire_pour_le_commerce_et_lindustrie", "bnp_paribas")
find("french_industrial_and_commercial_bank", "credit_mutuel")
find("monabanq", "credit_mutuel")

find("banque_cic_ouest", "french_industrial_and_commercial_bank")
find("banque_scalbertdupont", "french_industrial_and_commercial_bank")
find("groupe_caisse_depargne", "bpce_group")

find("banque_palatine", "bpce_group")
find("credit_foncier_de_france", "bpce_group")


find("halifax", "lloyds_banking_group_plc")
find("ceskoslovenska_obchodna_banka", "kbc")
find("kh_bank", "kbc")
find("banco_de_chile", "citi")
find("comdirect", "commerzbank")
find("komercni_banka", "societe_generale")
find("csob", "kbc")
find("ceska_sporitelna", "erste_group_bank_ag")
find("mbank", "commerzbank")
