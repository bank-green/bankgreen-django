from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import escape, format_html

from cities_light.models import Country, Region, SubRegion


class LinkedDatasourcesFilter(admin.SimpleListFilter):
    title = "Linked Datasources"
    parameter_name = "Linked Datasources"

    def lookups(self, request, model_admin):
        return (("Linked", "Linked"), ("Unlinked", "Unlinked"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Linked":
            brand_pks = [x.brand.pk for x in Datasource.objects.filter(brand__isnull=False)]
            return queryset.filter(pk__in=brand_pks)
        if value == "Unlinked":
            brand_pks = [x.brand.pk for x in Datasource.objects.filter(brand__isnull=False)]
            return queryset.exclude(pk__in=brand_pks)
        return queryset


def link_datasources(datasources, datasource_str):
    links = []
    filtered_datasources = [x for x in datasources if hasattr(x, datasource_str)]
    for ds in filtered_datasources:
        url = reverse("admin:%s_%s_change" % ("datasource", datasource_str), args=(ds.id,))
        string_to_show = escape(f"{datasource_str}: {ds.name}")
        link = format_html(f'<a href="{url}" />{string_to_show}</a>')
        links.append(link)
    return links


def link_contacts(contacts=None):
    links = []
    if contacts:
        for contact in contacts:
            url = reverse("admin:%s_%s_change" % ("brand", "contact"), args=(contact.id,))
            string_to_show = escape(f"{contact.email}")
            link = format_html(f'<a href="{url}" / style="font-Size: 14px">{string_to_show}</a>')
            links.append(link)
    else:
        url = reverse("admin:%s_%s_changelist" % ("brand", "contact"))
        link = format_html(
            f'<br></br><a href="{url}" / style="font-Size: 14px">Add contact emails</a>'
        )
        links.append(link)
    return links


def raise_validation_error_for_missing_country(self):
    regions_qs = self.cleaned_data.get("regions", Region.objects.none())
    expected_country_ids = set([x["country_id"] for x in regions_qs.values()])
    expected_country_iso2 = set(
        [x.code2 for x in Country.objects.filter(id__in=expected_country_ids)]
    )

    actual_countries_iso2 = set([x for x in self.cleaned_data.get("countries", [])])
    # validation hack for when datasources don't have "countries" defined, but only "country"
    if single_country := self.cleaned_data.get("country"):
        actual_countries_iso2.add(single_country)

    if not expected_country_iso2.issubset(actual_countries_iso2):
        missing_country_codes = expected_country_iso2 - actual_countries_iso2
        missing_country_names = ", ".join(
            [x.name for x in Country.objects.filter(code2__in=missing_country_codes)]
        )

        raise ValidationError(
            f"All regions must have associated countries. The following countries are missing: {missing_country_names}"
        )


def raise_validation_error_for_missing_region(self):
    regions_qs = self.cleaned_data.get("regions", Region.objects.none())
    subregions_qs = self.cleaned_data.get("subregions", SubRegion.objects.none())
    expected_regions = set([x.region for x in subregions_qs])

    if not expected_regions.issubset(set(regions_qs)):
        missing_regions = expected_regions - set(regions_qs)
        missing_region_names = " | ".join([x.display_name for x in missing_regions])

        raise ValidationError(
            f"All subregions must have associated regions. The following subregions are missing: {missing_region_names}"
        )
