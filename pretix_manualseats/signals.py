from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.control.signals import nav_event, nav_organizer

seat_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="14" viewBox="0 0 4.7624999 3.7041668" class="svg-icon"><path d="m 1.9592032,1.8522629e-4 c -0.21468,0 -0.38861,0.17394000371 -0.38861,0.38861000371 0,0.21466 0.17393,0.38861 0.38861,0.38861 0.21468,0 0.3886001,-0.17395 0.3886001,-0.38861 0,-0.21467 -0.1739201,-0.38861000371 -0.3886001,-0.38861000371 z m 0.1049,0.84543000371 c -0.20823,-0.0326 -0.44367,0.12499 -0.39998,0.40462997 l 0.20361,1.01854 c 0.0306,0.15316 0.15301,0.28732 0.3483,0.28732 h 0.8376701 v 0.92708 c 0,0.29313 0.41187,0.29447 0.41187,0.005 v -1.19115 c 0,-0.14168 -0.0995,-0.29507 -0.29094,-0.29507 l -0.65578,-10e-4 -0.1757,-0.87644 C 2.3042533,0.95300523 2.1890432,0.86500523 2.0641032,0.84547523 Z m -0.58549,0.44906997 c -0.0946,-0.0134 -0.20202,0.0625 -0.17829,0.19172 l 0.18759,0.91054 c 0.0763,0.33956 0.36802,0.55914 0.66042,0.55914 h 0.6015201 c 0.21356,0 0.21448,-0.32143 -0.003,-0.32143 H 2.1954632 c -0.19911,0 -0.36364,-0.11898 -0.41341,-0.34107 l -0.17777,-0.87126 c -0.0165,-0.0794 -0.0688,-0.11963 -0.12557,-0.12764 z"></path></svg>'


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
        },
    ]


@receiver(nav_organizer, dispatch_uid="manualseats_orga_nav")
def control_nav_orga_manualseats(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_organizer_permission(request.organizer, "can_change_organizer_settings", request=request):
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
