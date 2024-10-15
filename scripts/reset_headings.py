from django.db.models import Q

from brand.models import *


# this script deletes redundant headings

great_headers = Commentary.objects.filter(header__icontains="great")
great_headers.filter(~Q(rating="great"))
# manually fix mismatches
for c in great_headers:
    c.header = ""
    c.save()


ok_headers = Commentary.objects.filter(header__icontains="ok")
ok_headers.filter(~Q(rating="ok"))
# manually fix mismatches
for c in ok_headers:
    c.header = ""
    c.save()

bad_headers = Commentary.objects.filter(header__icontains="bad")
bad_headers.filter(~Q(rating="bad"))
# manually fix mismatches
for c in bad_headers:
    c.header = ""
    c.save()


worst_headers = Commentary.objects.filter(header__icontains="worst")
worst_headers.filter(~Q(rating="worst"))
# manually fix mismatches
for c in worst_headers:
    c.header = ""
    c.save()
