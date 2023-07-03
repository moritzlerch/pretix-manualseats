from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from pretix.base.forms import I18nModelForm
from pretix.base.models import SeatingPlan
from pretix.control.permissions import (
    EventPermissionRequiredMixin,
    OrganizerPermissionRequiredMixin,
)
from pretix.helpers.compat import CompatDeleteView
from pretix.helpers.models import modelcopy


class EventIndex(EventPermissionRequiredMixin, TemplateView):
    model = SeatingPlan
    # context_object_name = "seatingplans"
    template_name = "pretix_manualseats/event/index.html"
    permission = "can_change_orders"

    def get_seatingplans(self):
        return SeatingPlan.objects.filter(organizer=self.request.organizer)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx["seatingplans"] = self.get_seatingplans()

        return ctx


class OrganizerSeatingPlanList(OrganizerPermissionRequiredMixin, ListView):
    model = SeatingPlan
    context_object_name = "seatingplans"
    paginate_by = 20
    template_name = "pretix_manualseats/organizer/index.html"
    permission = "can_change_organizer_settings"

    def get_queryset(self):
        return SeatingPlan.objects.filter(organizer=self.request.organizer).order_by(
            "id"
        )


class SeatingPlanForm(I18nModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = SeatingPlan
        fields = ("name", "layout")


class SeatingPlanDetailMixin:
    def get_object(self, queryset=None) -> SeatingPlan:
        try:
            return SeatingPlan.objects.get(
                organizer=self.request.organizer, id=self.kwargs["seatingplan"]
            )
        except SeatingPlan.DoesNotExist:
            raise Http404(_("The requested seating plan does not exist."))

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_manualseats:index",
            kwargs={"organizer": self.request.organizer.slug},
        )


# class OrganizerPlanAdd(OrganizerPermissionRequiredMixin, CreateView):
#     model = SeatingPlan
#     form_class = SeatingPlanForm
#     template_name = "pretix_manualseats/organizer/form.html"
#     permission = "can_change_organizer_settings"

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data()
#         return ctx

#     def get_success_url(self) -> str:
#         return reverse(
#             "plugins:pretix_manualseats:index",
#             kwargs={
#                 "organizer": self.request.organizer.slug,
#             },
#         )

#     @transaction.atomic
#     def form_valid(self, form):
#         form.instance.organizer = self.request.organizer
#         messages.success(self.request, _("The new seating plan has been added."))
#         ret = super().form_valid(form)
#         form.instance.log_action(
#             "pretix_seatingplan.seatingplan.added",
#             data=dict(form.cleaned_data),
#             user=self.request.user,
#         )
#         self.request.organizer.cache.clear()
#         return ret

#     def form_invalid(self, form):
#         messages.error(self.request, _("Your changes could not be saved."))
#         return super().form_invalid(form)


class OrganizerPlanAdd(OrganizerPermissionRequiredMixin, CreateView):
    model = SeatingPlan
    form_class = SeatingPlanForm
    template_name = "pretix_manualseats/organizer/form.html"
    permission = "can_change_organizer_settings"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_manualseats:index",
            kwargs={
                "organizer": self.request.organizer.slug,
            },
        )

    @transaction.atomic
    def form_valid(self, form):
        form.instance.organizer = self.request.organizer
        messages.success(self.request, _("The new seating plan has been added."))
        ret = super().form_valid(form)
        form.instance.log_action(
            "pretix_seatingplan.seatingplan.added",
            data=dict(form.cleaned_data),
            user=self.request.user,
        )
        self.request.organizer.cache.clear()
        return ret

    def form_invalid(self, form):
        messages.error(self.request, _("Your changes could not be saved."))
        return super().form_invalid(form)

    @cached_property
    def copy_from(self):
        if self.request.GET.get("copy_from") and not getattr(self, "object", None):
            try:
                return SeatingPlan.objects.get(
                    organizer=self.request.organizer,
                    id=self.request.GET.get("copy_from"),
                )
            except SeatingPlan.DoesNotExist:
                raise Http404(
                    _("The requested seating plan does not exist. Can't copy!")
                )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.copy_from:
            i = modelcopy(self.copy_from)
            i.id = None
            i.name += " (Copy)"
            kwargs["instance"] = i
            kwargs.setdefault("initial", {})
        return kwargs


# class LayoutCreate(EventPermissionRequiredMixin, CreateView):
#     @transaction.atomic
#     def form_valid(self, form):
#         form.instance.event = self.request.event
#         if not self.request.event.badge_layouts.filter(default=True).exists():
#             form.instance.default = True
#         messages.success(self.request, _("The new badge layout has been created."))
#         super().form_valid(form)
#         if form.instance.background and form.instance.background.name:
#             form.instance.background.save("background.pdf", form.instance.background)

#     def get_context_data(self, **kwargs):
#         return super().get_context_data(**kwargs)

#     @cached_property
#     def copy_from(self):
#         if self.request.GET.get("copy_from") and not getattr(self, "object", None):
#             try:
#                 return self.request.event.badge_layouts.get(pk=self.request.GET.get("copy_from"))
#             except BadgeLayout.DoesNotExist:
#                 pass

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()

#         if self.copy_from:
#             i = modelcopy(self.copy_from)
#             i.pk = None
#             i.default = False
#             kwargs["instance"] = i
#             kwargs.setdefault("initial", {})
#         return kwargs


class OrganizerPlanEdit(
    OrganizerPermissionRequiredMixin, SeatingPlanDetailMixin, UpdateView
):
    model = SeatingPlan
    form_class = SeatingPlanForm
    template_name = "pretix_manualseats/organizer/form.html"
    permission = "can_change_organizer_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_manualseats:index",
            kwargs={
                "organizer": self.request.organizer.slug,
            },
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _("Your changes have been saved."))
        if form.has_changed():
            self.object.log_action(
                "pretix_seatingplan.seatingplan.changed",
                data=dict(form.cleaned_data),
                user=self.request.user,
            )
        self.request.organizer.cache.clear()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Your changes could not be saved."))
        return super().form_invalid(form)


class OrganizerPlanDelete(
    OrganizerPermissionRequiredMixin, SeatingPlanDetailMixin, CompatDeleteView
):
    model = SeatingPlan
    template_name = "pretix_manualseats/organizer/delete.html"
    context_object_name = "seatingplan"
    permission = "can_change_organizer_settings"

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.log_action(
            "pretix_manualseats.seatingplan.deleted", user=self.request.user
        )
        self.object.delete()
        messages.success(request, _("The selected plan has been deleted."))
        self.request.organizer.cache.clear()
        return HttpResponseRedirect(self.get_success_url())
