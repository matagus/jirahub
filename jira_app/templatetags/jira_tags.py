from datetime import datetime

from django import template
from django.contrib.humanize.templatetags.humanize import naturalday


register = template.Library()


@register.filter
def natural_day(value):
    if (value is None) or (value == ""):
        return ""

    dt = datetime.fromisoformat(value.split(".")[0])
    return naturalday(dt)


@register.filter
def to_status_class(category):
    return dict(done="tag--success", new="tag--primary", indeterminate="tag--info").get(category, "tag--white")


@register.filter
def to_issue_type_class(type_name):
    type_name_lower = type_name.lower()

    if "back" in type_name_lower:
        return "tag--link"
    elif "front" in type_name_lower:
        return "tag--black"
    elif "ux" in type_name_lower:
        return "tag--warning"
    else:
        return "tag--info"


@register.filter
def to_sprint_state_class(state):
    return dict(
        closed="tag--black",
        active="tag--success",
    ).get(state, "tag--white")
