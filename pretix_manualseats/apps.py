from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import __version__


class PluginApp(AppConfig):
    name = "pretix_manualseats"
    verbose_name = "Manual Seats"

    class PretixPluginMeta:
        name = _("Manual Seats")
        author = "Moritz Lerch, Mark Oude Elberink"
        description = _("Manually assign tickets to seats.")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=4.16.0"

    def ready(self):
        from . import signals  # NOQA

    def installed(self, event):
        event.settings.seating_choice = False  # hierarkey speichert selber
