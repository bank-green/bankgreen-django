import json, re, requests, time
from brand.models import Brand, Commentary
from unidecode import unidecode
from django.urls import reverse
import itertools


prismic_base_url = "https://bankgreen.cdn.prismic.io/api/v2"
prismic_filter_documents_url = "/documents/search"


def get_ref_id():

    try:
        response = requests.get(prismic_base_url)
        if response.status_code == 200:
            response = response.json()
            print(f"reference number is : {response['refs'][0]['ref']}")
            return response["refs"][0]["ref"]
        else:
            print(response.status_code)
            print(response.json())
            return None
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def get_prismic_documents(document_type, ref_number):

    bank_uids = []

    if (not document_type) or (not ref_number):
        print(f"Error message : Please provide the document_type and reference number")
        return None

    # document_url = prismic_filter_documents_url.replace("DOCUMENTTYPE", document_type.lower()).replace('RRRR', ref_number).replace('PGNUMBER', pg_number)
    params = {"q": f'[[at(document.type,"{document_type}")]]', "ref": ref_number, "page": 1}
    url = prismic_base_url + prismic_filter_documents_url

    while url:

        try:
            response = requests.get(url, params=params)

            params = None
            if response.status_code == 200:
                response_body = response.json()

                for result in response_body["results"]:
                    bank_uids.append(result["uid"])

                url = response_body["next_page"]
            else:
                return bank_uids
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

    return bank_uids


def calculate_missing_tags(list_brand_tags, list_prismic_pages, find_missing_brands_flag=False):
    """
    Returns missing brands and pages
    """

    # make it lowercase
    tag_dict = {ele.lower(): ele for ele in list_brand_tags}
    prsimic_page_dict = {ele.lower(): ele for ele in list_prismic_pages}

    # make a list of brand tags and prismic pages
    set_brand_tags = set(list(tag_dict.keys()))
    set_prismic_pages = set(list(prsimic_page_dict.keys()))

    # perform set difference to find out missing
    if find_missing_brands_flag:
        return set_prismic_pages.difference(set_brand_tags)

    missing_bank_pages = set_brand_tags.difference(set_prismic_pages)
    return [tag_dict[ele] for ele in missing_bank_pages]


def get_missing_brand_and_bankpages(ref):
    """
    Finds the missing brands for which accompanying bankpages are present in prismic
    Finds the missing bankpages for which accompanying brands are present in bank.green
    """
    output_dict = {}

    # Make an API call to fetch all BankPages from PRISMIC
    list_prismic_bankpage_tags = get_prismic_documents("bankpage", ref)
    list_prismic_bankpage_tags = [ele.strip() for ele in list_prismic_bankpage_tags]

    # Fetch all brands
    list_brand_tags = list(Brand.objects.values_list("tag", flat=True))
    # list_brand_tags = [ele.strip() for ele in list_brand_tags]

    output_dict["missing_brands"] = calculate_missing_tags(
        list_brand_tags, list_prismic_bankpage_tags, find_missing_brands_flag=True
    )
    missing_bank_pages = calculate_missing_tags(list_brand_tags, list_prismic_bankpage_tags)

    output_dict["missing_bank_pages"] = []
    for tag in missing_bank_pages:
        try:
            output_dict["missing_bank_pages"].append(
                (tag, reverse("admin:brand_brand_change", args=[tag]))
            )
        except:
            output_dict["missing_bank_pages"].append((tag, None))

    output_dict["missing_brands"] = sorted(output_dict["missing_brands"])
    output_dict["missing_bank_pages"] = sorted(output_dict["missing_bank_pages"])

    return output_dict


def get_missing_sfi_brands_and_pages(ref):
    """
    Finds the missing sfi brands for which accompanying sfi pages are present in prismic
    Finds the missing sfi pages for which accompanying sfi brands are present in bank.green
    """
    output_dict = {}

    # Make an API call to fetch all BankPages from PRISMIC
    list_prismic_sfipage_tags = get_prismic_documents("sfipage", ref)
    list_prismic_sfipage_tags = [ele.strip() for ele in list_prismic_sfipage_tags]

    # Fetch all SFI brands
    brand_ids = list(
        Commentary.objects.filter(show_on_sustainable_banks_page=True).values_list(
            "brand_id", flat=True
        )
    )
    list_of_sfi_brand_tags = [Brand.objects.values("tag").get(pk=id)["tag"] for id in brand_ids]
    list_of_sfi_brand_tags = [ele.strip() for ele in list_of_sfi_brand_tags]

    output_dict["sfi_missing_brands"] = calculate_missing_tags(
        list_of_sfi_brand_tags, list_prismic_sfipage_tags, find_missing_brands_flag=True
    )
    output_dict["sfi_missing_brands"] = sorted(output_dict["sfi_missing_brands"])

    missing_sfi_pages = calculate_missing_tags(list_of_sfi_brand_tags, list_prismic_sfipage_tags)

    output_dict["missing_sfi_pages"] = []
    for tag in missing_sfi_pages:
        try:
            output_dict["missing_sfi_pages"].append(
                (tag, reverse("admin:brand_brand_change", args=[tag]))
            )
        except:
            output_dict["missing_sfi_pages"].append((tag, None))

    output_dict["missing_sfi_pages"] = sorted(output_dict["missing_sfi_pages"])

    return output_dict
