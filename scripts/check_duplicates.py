from symspellpy import SymSpell, Verbosity
from brand.models import Brand
from django.urls import reverse

def return_all_duplicates() :
    #fetch all brands from Brand.models
    all_objects = Brand.objects.all()

    name_comparison = SymSpell()
    tag_comparison = SymSpell()
    name_to_pk = {}

    #For each object add its name and tag to dictionary and map them to Object.pk
    for object in all_objects:
        name_comparison.create_dictionary_entry(object.name, 1)
        tag_comparison.create_dictionary_entry(object.tag, 1)
        name_to_pk[object.name] = object.pk 
        name_to_pk[object.tag] = object.pk

    relation_dictionary = {}

    #Find all relations and them with their Pk to the relation diictionary

    for object in all_objects:
        name_matches = name_comparison.lookup(object.name, Verbosity.ALL)
        tag_matches = tag_comparison.lookup(object.tag, Verbosity.ALL)

        relation_dictionary[object.name] = []

        for possible_match in name_matches[1:] + tag_matches[1:] :
            relation_dictionary[object.name].append([possible_match.term, reverse("admin:brand_brand_change", args=(str(name_to_pk[possible_match.term]),))])

    return relation_dictionary
