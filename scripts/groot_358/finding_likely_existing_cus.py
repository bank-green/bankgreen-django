from brand.models import *
from brand.models.commentary import InstitutionType


"""
This is a script to help us find credit unions that are already in DBG and go through them by hand
"""

cu_names = [
    "Australian Central Credit Union Ltd",
    "Community First Credit Union Ltd",
    "Goulbum Murray Credit Union Co-operative",
    "Illawarra Credit Union Limited",
    "Macquarie Credit Union Limited",
    "Northen Inland Credit Union",
    "Orange Credit Union Limited",
    "Police Credit Union Limited",
    "Pulse Credit Union Limited",
    "Railways Credit Union Limited",
    "South-West Credit Union Co-operative",
    "The Broken Hill Community Credit Union",
    "Traditional Credit Union Limited",
    "WAW Credit Union Co-operative",
    "Australian Military Bank",
    "IMB Bank",
]


australian_brands = Brand.objects.all()


CU = InstitutionType.objects.get(name="Credit Union")


positives = {}
for name in cu_names:
    name = (
        name.lower()
        .replace("credit union", "")
        .replace(" ltd", "")
        .replace("Limited", "")
        .replace("Bank", "")
        .replace("Co-operative", "")
        .strip()
    )

    matches = australian_brands.filter(name__contains=name).filter(countries__contains="AU")

    for x in matches:
        commentary = Commentary.objects.get_or_create(brand=x)

    # matches = [x for x in matches if x.commentary.institution_type.filter(pk=CU.pk).exists()]

    if len(matches) > 0:
        positives[name] = [x.tag for x in matches]

from pprint import pprint


pprint(positives)
