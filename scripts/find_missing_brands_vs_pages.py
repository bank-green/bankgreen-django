import json, re, requests, time
from brand.models import Brand, Commentary
from unidecode import unidecode

# read json response from the api call


prismic_base_url = "https://bankgreen.cdn.prismic.io/api/v2"
prismic_filter_documents_url = "/documents/search"


def get_ref_id():

	try:
		response = requests.get(prismic_base_url)
		if response.status_code == 200:
			response = response.json()
			print(f"reference number is : {response['refs'][0]['ref']}")
			return response['refs'][0]['ref']
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
	params = {'q':f'[[at(document.type,"{document_type}")]]', 'ref': ref_number, "page":1}
	url = prismic_base_url + prismic_filter_documents_url

	while url:

		try: 
			response = requests.get(url, params = params)
			
			params = None
			if response.status_code == 200:
				response_body = response.json()
	
				for result in response_body["results"]:
					bank_uids.append(result["uid"])
					# if result["uid"] == "sfi_credit_cooperatif":
					# 	print(f"================url =============== {url}")
				url = response_body["next_page"]
			else:
				return bank_uids
		except requests.exceptions.RequestException as e:
			raise SystemExit(e)

	return bank_uids

def get_dict(data):

	return {re.sub('[^A-Za-z0-9]+','', tag ).lower(): tag for tag in data if not tag.isalpha()}


def calculate_missing_pages(brand_tags, prismic_page_tags, brand_names):

	set_brand_tags = set(brand_tags)
	set_prismic_page_tags = set(prismic_page_tags)
	set_brand_names = set(brand_names)

	set_union = set_brand_tags.union(set_brand_names)
	set_diff = set_union.difference(set_prismic_page_tags)

	print("==========================prismic bank pages ====================")
	print(set_prismic_page_tags)


	print("=====================set brand names ===================")
	print(set_brand_names)

	print("=====================set union ===================")
	print(set_union)

	print("=====================set diff ===================")
	print(set_diff)

	tag_name_map = {tag: name for tag, name in zip(brand_tags, brand_names)}

	print("=====================Tag Name Map===================")
	print(tag_name_map)



	result = []

	for ele in set_diff:
		if ele in set_brand_names:
			result.append(ele)
		elif ele in set_brand_tags:
			result.append(tag_name_map[ele])



	print(f"=======================missing bank pages ===================")
	print(result)

	return result


def calculate_missing_brands(brand_tags, prismic_page_tags, brand_names):
	# missing_bankpages = []
	missing_brands = []
	# diff_tags = {}

	set_brand_tags = set(brand_tags)
	set_prismic_page_tags = set(prismic_page_tags)
	set_brand_names = set(brand_names)

	# print("======================PRISMIC=======================")
	# print(set_prismic_page_tags)

	# print(f"====================UNION======================")
	# print(set_brand_tags.union(set_brand_names))



	missing_brands = set_prismic_page_tags - (set_brand_tags.union(set_brand_names))

	# tags_present_only_in_prismic1 = set_prismic_page_tags - set_brand_names
	# tags_present_only_in_prismic2 = set_prismic_page_tags - set_brand_tags

	# missing_brands = tags_present_only_in_prismic1.intersection(tags_present_only_in_prismic2)

	# dict_brand_tags = get_dict(brand_tags)
	# dict_prismic_page_tags = get_dict(prismic_page_tags)

	# set_missing_brand_vs_pages = set_brand_tags.union(set_prismic_page_tags) - set_brand_tags.intersection(set_prismic_page_tags)


	# for ele in set_missing_brand_vs_pages:


	# 	tmp = re.sub('[^A-Za-z0-9]+','', ele).lower()
	# 	try:
	# 		if dict_prismic_page_tags[tmp] and dict_brand_tags[tmp] :
	# 			# and (dict_prismic_page_tags[tmp] not in diff_tag.keys()) and (dict_brand_tags[tmp] not in diff_tag.values()
	# 			# diff_tags.append(f"dict_prismic_page_tags {dict_prismic_page_tags[tmp]} is different from dict_brand_tags {dict_brand_tags[tmp]}")
	# 			diff_tags[dict_prismic_page_tags[tmp]]=dict_brand_tags[tmp]
	# 			continue
	# 	except KeyError as ke:
	# 		pass
	# 	if ele in set_brand_tags:
	# 		missing_bankpages.append(ele)
	# 	else: 
	# 		missing_brands.append(ele)

	# missing_bankpages.sort()
	# missing_brands.sort()

	# return missing_bankpages, missing_brands, diff_tags
	# print(f"==========missing brands==============")
	# print(missing_brands)
	return missing_brands

def return_missing_brand_vs_bankpage():

	output_dict = {}
	ref = get_ref_id()

	# Make an API call to fetch all BankPages from PRISMIC
	before = time.time()
	print("Before-----> ", before)
	list_prismic_bankpage_tags = get_prismic_documents("bankpage", ref)
	list_prismic_bankpage_tags = [ele.strip() for ele in list_prismic_bankpage_tags]
	list_prismic_bankpage_tags = [re.sub('[\s\-]+','_', ele).lower() for ele in list_prismic_bankpage_tags]
	list_prismic_bankpage_tags = [re.sub('[^A-Za-z0-9\_]+','', ele) for ele in list_prismic_bankpage_tags]
	after = time.time()
	print("After-----> ", after)
	print(f'-----------diff {int(after - before)}')

	
	# Fetch all brands
	list_brand_tags = list(Brand.objects.values_list("tag", flat=True))

	# print(f"=============TAGS===================")
	# for ele in list_brand_tags:
	# 	if ele.isascii() == False:
	# 		print(ele)

	list_brand_tags = [unidecode(ele) if ele.isascii() == False else ele for ele in list_brand_tags ]
	list_brand_tags = [ele.strip() for ele in list_brand_tags]

	list_brand_tags = [re.sub('[\s\-]+','_', ele).lower() for ele in list_brand_tags]
	list_brand_tags = [re.sub('[^A-Za-z0-9\_]+','', ele) for ele in list_brand_tags]
	

	# list_brand_tags.sort(key=str.casefold)

	list_brand_names = list(Brand.objects.values_list("name", flat=True))

	# print(f"=============NAMES===================")
	# for ele in list_brand_names:
	# 	if ele.isascii() == False:
	# 		print(ele)

	list_brand_names = [unidecode(ele) if (not ele.isascii()) else ele for ele in list_brand_names]
	list_brand_names = [ele.strip() for ele in list_brand_names]
	list_brand_names= [re.sub('[\s\-]+','_', ele).lower() for ele in list_brand_names]
	list_brand_names = [re.sub('[^A-Za-z0-9\_]+','', ele).lower() for ele in list_brand_names]
	

	# list_brand_names.sort(key=str.casefold)


	list_sfi_bankpage_tags = get_prismic_documents("sfipage", ref)
	# print(f"----------------------API output ------------------")
	# print(list_sfi_bankpage_tags)
	list_sfi_bankpage_tags = [ele.strip() for ele in list_sfi_bankpage_tags]
	list_sfi_bankpage_tags = [re.sub('[\s\-]+','_', ele).lower() for ele in list_sfi_bankpage_tags]
	list_sfi_bankpage_tags = [re.sub('[^A-Za-z0-9\_]+','', ele) for ele in list_sfi_bankpage_tags]

	# Fetch all SFI brands 
	brand_ids = list(Commentary.objects.filter(show_on_sustainable_banks_page=True).values_list("brand_id", flat=True))
	list_of_sfi_brand_tags = [Brand.objects.values("tag").get(pk=id)["tag"] for id in brand_ids]
	list_of_sfi_brand_tags = [unidecode(ele) if ele.isascii() == False else ele for ele in list_of_sfi_brand_tags ]
	list_of_sfi_brand_tags = [ele.strip() for ele in list_of_sfi_brand_tags]

	list_of_sfi_brand_tags = [re.sub('[\s\-]+','_', ele).lower() for ele in list_of_sfi_brand_tags]
	list_of_sfi_brand_tags = [re.sub('[^A-Za-z0-9\_]+','', ele) for ele in list_of_sfi_brand_tags]
	
	# list_of_sfi_brand_tags.sort(key=str.casefold)
	
	# output_dict["missing_bankpages"], output_dict["missing_brands"], output_dict["diff_tag"] = calculate_missing_brands_pages(list_brand_tags, list_prismic_bankpage_tags)

	output_dict["missing_brands"] = calculate_missing_brands(list_brand_tags, list_prismic_bankpage_tags, list_brand_names)
	output_dict["sfi_missing_brands"] = calculate_missing_brands(list_of_sfi_brand_tags, list_sfi_bankpage_tags, list_brand_names)
	output_dict["missing_bankpages"] = calculate_missing_pages(list_brand_tags, list_prismic_bankpage_tags, list_brand_names)
	# output_dict["sfi_missing_bankpages"], output_dict["sfi_missing_brands"], output_dict["sfi_diff_tag"] = calculate_missing_brands_pages(list_of_sfi_brand_tags, list_sfi_bankpage_tags)

	output_dict["missing_brands"] = sorted(output_dict["missing_brands"])
	output_dict["sfi_missing_brands"] = sorted(output_dict["sfi_missing_brands"])

	print(len(output_dict["missing_brands"]))
	print(len(output_dict["sfi_missing_brands"]))
	print(len(output_dict["missing_bankpages"]))
	# print(len(output_dict["diff_tag"]))

	return output_dict



