from django.contrib.staticfiles import finders
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.control.signals import nav_event, nav_organizer

seat_icon = open(finders.find("pretix_manualseats/icons/seat.svg", all=False)).read()


@receiver(nav_event, dispatch_uid="manualsets_nav")
def control_nav_manualseats(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_event_permission(
        request.organizer, request.event, "can_change_event_settings", request=request
    ):
        return []
    return [
        {
            "label": _("Manual Seats"),
            "url": reverse(
                "plugins:pretix_manualseats:index",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.event.organizer.slug,
                },
            ),
            "active": (url.namespace == "plugins:pretix_manualseats"),
            "icon": seat_icon,
            "children":[
                {
                    "label": _("Seating mapping"),
                    "url": reverse(
                        "plugins:pretix_manualseats:mapping",
                        kwargs={
                            "event": request.event.slug,
                            "organizer": request.organizer.slug,
                        },
                    ),
                    "active": (url.namespace == "plugins:pretix_manualseats"),
                    "icon": seat_icon,
                    
                },
            ]
        },
    ]


@receiver(nav_organizer, dispatch_uid="manualseats_orga_nav")
def control_nav_orga_manualseats(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_organizer_permission(
        request.organizer, "can_change_organizer_settings", request=request
    ):
        return []
    if not request.organizer.events.filter(plugins__icontains="pretix_manualseats"):
        return []
    return [
        {
            "label": _("Seating Plans"),
            "url": reverse(
                "plugins:pretix_manualseats:index",
                kwargs={
                    "organizer": request.organizer.slug,
                },
            ),
            "active": (url.namespace == "plugins:pretix_manualseats"),
            "icon": seat_icon,
        },
    ]
