from brand.models import Commentary, Brand, BrandFeature
from brand.models.commentary import InstitutionCredential, InstitutionType


def get_brand_data():
    """
    Retrieve all Brand data from the database.
    """
    return Brand.objects.all()


def get_institution_data():
    """
    Retrieve all Institute data from the database.
    """
    return InstitutionType.objects.all(), InstitutionCredential.objects.all()


def concat_brand_feature_data(brand_id):
    """
    Return concatenated brand feature data fieldwise.
    """
    data_dict = {}

    brand_feature_data = BrandFeature.objects.filter(brand_id=brand_id)

    if brand_feature_data:
        data_dict["brand_feature_id"] = ",".join([str(x.id) for x in brand_feature_data])
        data_dict["feature"] = ",".join([str(x.feature) for x in brand_feature_data])

    return data_dict


def concat_commentary_data(brand_id):
    """
    Return concatenated commentary data fieldwise.
    """
    data_dict = {}

    commentary_data = Commentary.objects.filter(brand_id=brand_id).values()

    commentary_fields = [field.name for field in Commentary._meta.get_fields()]
    commentary_fields[2] = "inherit_brand_rating_id"

    if commentary_data:
        for field in commentary_fields:
            if field == "id":
                data_dict["commentary_id"] = ",".join(
                    [str(commentary_data[idx][field]) for idx in range(len(commentary_data))]
                )
                continue
            if (
                field != "brand"
                and field != "institution_type"
                and field != "institution_credentials"
            ):
                data_dict[field] = ",".join(
                    [
                        str(commentary_data[idx][field])
                        if type(commentary_data[idx][field]) != str
                        else commentary_data[idx][field]
                        for idx in range(len(commentary_data))
                    ]
                )

    return data_dict
