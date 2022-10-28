from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.0.0"


class PluginApp(PluginConfig):
    name = "seating_plan"
    verbose_name = "Seating Plan"

    class PretixPluginMeta:
        name = gettext_lazy("Seating Plan")
        author = "Evey"
        description = gettext_lazy("Ticket buyers can choose their own seats on an interactive seating plan. We can handle every venue from small cinemas or ballrooms up to large-scale stadiums.")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = "seating_plan.PluginApp"
