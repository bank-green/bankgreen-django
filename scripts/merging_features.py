from brand.models import *


# This code takes one FeatureType and merges all instances of BrandFeatures with that FeatureType
# into FeatureType. In instances where the BrandFeature didn't already exist, it creates one

mb = FeatureType.objects.get(name="Mobile banking")
online_banking = FeatureType.objects.get(name="online_banking")

obfs = BrandFeature.objects.filter(feature=online_banking)


for obf in obfs:
    try:
        already_done = BrandFeature.objects.get(brand=obf.brand, feature=mb)
    except Exception as e:
        BrandFeature.objects.create(brand=obf.brand, feature=mb)
        print(f"new feature created on {obf.brand}")
