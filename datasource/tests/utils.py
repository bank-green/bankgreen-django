from datasource.models.usnic import Usnic


def create_test_usnic():
    # rssd needs to be the same so that this will match with a brand with the same rssd
    usnic1 = Usnic.objects.create(id=1000, name="test parent", rssd="test rssd")
    usnic2 = Usnic.objects.create(
        id=2000, name="Another Brand 2", rssd="somerandomstuffshouldnevermatch239023900939009"
    )
    usnic3 = Usnic.objects.create(id=3000, name="atestb", rssd="6817896186")
    usnic4 = Usnic.objects.create(
        id=4000, name="veryunusualnameshouldnotbeassociated", rssd="9820394845e"
    )

    return (usnic1, usnic2, usnic3, usnic4)
