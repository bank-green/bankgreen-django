from django import template
from reversion.models import Version, Revision

from brand.models.brand import Brand

register = template.Library()

@register.inclusion_tag('admin/brand/brand/revision_table.html')
def render_revision_table(action_list):
    brand_id = action_list[0]['url'].split('/')[4]
    reversion_ids = [x.id + 1 for x in Version.objects.get_for_object_reference(Brand, brand_id)]
    reversion_ratings = [Version.objects.get(id=reversion_id).field_dict['rating'] for reversion_id in reversion_ids]
    for i in range(len(action_list)):
        action_list[i]['rating'] = reversion_ratings[i]
    return { 'action_list': action_list }
