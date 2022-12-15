from ..models import Brand


def create_test_brands():
    brand1 = Brand.objects.create(
        pk=100,
        tag="test_brand_1",
        name="Test Brand 1",
        aliases="test brand, testb",
        website="www.testbrand.com",
        permid="test permid",
        viafid="test viafid",
        lei="test lei",
        rssd="test rssd",
    )

    brand2 = Brand.objects.create(
        pk=200,
        tag="another_brand_2",
        name="Another Brand 2",
        aliases="another brand, anotherb",
        website="https://www.anotherbwebsite.com/somepage",
        permid="another permid",
        viafid="another viafid",
        lei="another lei",
        rssd="another rssd",
    )

    return (brand1, brand2)
