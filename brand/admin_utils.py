from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import escape, format_html


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
