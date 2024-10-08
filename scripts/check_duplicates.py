from django.urls import reverse

from symspellpy import SymSpell, Verbosity

from brand.models import Brand


def return_all_duplicates():
    # fetch all brands from Brand.models
    all_objects = Brand.objects.all()

    name_comparison = SymSpell()
    tag_comparison = SymSpell()
    name_or_tag_to_pk = {}
    pk_to_name = {}

    # For each object add its name and tag to dictionary and map them to pk and then map each pk to a name
    for object in all_objects:
        name_comparison.create_dictionary_entry(object.name, 1)
        tag_comparison.create_dictionary_entry(object.tag, 1)
        name_or_tag_to_pk[object.name] = object.pk
        name_or_tag_to_pk[object.tag] = object.pk
        pk_to_name[object.pk] = object.name

    relation_dictionary = {}

    # Find all relations and then add a tuple of object name and url to dictionary

    for object in all_objects:
        name_matches = name_comparison.lookup(object.name, Verbosity.ALL)
        tag_matches = tag_comparison.lookup(object.tag, Verbosity.ALL)
        source_object_url = reverse("admin:brand_brand_change", args=(str(object.pk),))
        relation_dictionary[(object.name, source_object_url)] = set()

        for possible_match in name_matches[1:] + tag_matches[1:]:
            possible_match_pk = name_or_tag_to_pk[possible_match.term]
            possible_match_name = pk_to_name[possible_match_pk]

            if possible_match_pk < object.pk:
                possible_match_url = reverse(
                    "admin:brand_brand_change", args=(str(possible_match_pk),)
                )
                relation_dictionary[(object.name, source_object_url)].add(
                    (possible_match_name, possible_match_url)
                )

    return relation_dictionary
