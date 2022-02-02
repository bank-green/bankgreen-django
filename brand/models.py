from django.db import models

# from datasource.models import Banktrack as bt
# from datasource.models import Datasource as ds

import datasource.models as dsm


class Brand(models.Model):
    """
    A "Brand" is the instance shown to the end user.
    Multiple Datasources may be associated with a single brand.
    The brand's charasterics are initially determined by the data sources.
    However, they may be overwritten by the user.
    """

    tag = models.CharField("Unique tag for the brand", max_length=100, unique=True, null=False, blank=False)
    name = models.CharField(
        "Name of the Bank brand to be displayed to the user", max_length=200, null=False, blank=False, default="unknown"
    )
    description = models.TextField(
        "Description of the bank brand to be displayed to the user", null=False, blank=True, default=""
    )

    snippet_1 = models.TextField("Custom fact about the brand.", help_text="Used to fill in templates")
    snippet_2 = models.TextField("Custom fact about the brand.", help_text="Used to fill in templates")
    snippet_3 = models.TextField("Custom fact about the brand.", help_text="Used to fill in templates")

    def refresh_name(self, overwrite_existing=False):
        # sometimes a preferred name is specified for a brand.
        # In that case, return the preferred name
        # If there is more than one, just randomly choose one.
        field_default = self.__class__.name.field.default

        if overwrite_existing and self.name != field_default:
            return

        # Favor Banktrack names
        if banktrack_datasources := dsm.Banktrack.objects.filter(brand=self):
            self.name = banktrack_datasources[0].name
            self.save()
        else:
            self.name = field_default
            self.save()

    # TODO: Figure out how I can deduplicate these refreshes, perhaps specifying a field and an order of Datasource type priority
    def refresh_description(self, overwrite_existing=False):
        field_default = self.__class__.description.field.default
        if overwrite_existing and self.description != field_default:
            return

        # Favor Banktrack descriptions
        if banktrack_datasources := dsm.Banktrack.objects.filter(brand=self):
            self.description = banktrack_datasources[0].description
            self.save()
        else:
            self.description = field_default
            self.save()

    def refresh(self, name=True, description=True, overwrite_existing=False):
        if name:
            self.refresh_name(overwrite_existing)
        if description:
            self.refresh_description(overwrite_existing)

    # TODO: Decide how tag should be stored or just generated

    # @property
    # def tag(self):
    #     # Check the id_tag_dict for entries. If there are entries there, return them.
    #     lookup_tag = self.bankreg.return_tag_from_id_tag_dict(
    #         permid=self.permid, isin=self.isin, viafid=self.viafid, lei=self.lei,
    #         googleid=self.googleid, wikiid=self.wikiid, rssd=self.rssd)
    #     if lookup_tag:
    #         return lookup_tag.lower()

    #     # check the name_tag_dict. If there is an entry there, return it.
    #     name_tag_dict = self.bankreg.name_tag_dict
    #     if name_tag_dict.get(self.name):
    #         return name_tag_dict.get(self.name).lower()

    #     # check the name_tag_dict for unidecoded names. If there is an entry there, return it.
    #     unidecoded_name = unidecode.unidecode(self.name)
    #     if name_tag_dict.get(unidecoded_name):
    #         return name_tag_dict.get(unidecoded_name).lower()

    #     # if all else fails, autogenerate a tag
    #     return self.autogenerate_tag().lower()
