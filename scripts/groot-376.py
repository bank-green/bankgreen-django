from brand.models import *

full_headlines = Commentary.objects.all().exclude(headline__isnull=True).exclude(headline='')
full_subtitles = Commentary.objects.all().exclude(subtitle__isnull=True).exclude(subtitle='')

tags = {x.brand.tag for x in full_headlines}.union({x.brand.tag for x in full_subtitles})

for tag in tags:
    print(tag)
    print(f"HEADLINE: {Brand.objects.get(tag=tag).commentary.headline}")
    print(f"SUBTITLE: {Brand.objects.get(tag=tag).commentary.subtitle}")
    print('----')

full_headlines.update(headline='')