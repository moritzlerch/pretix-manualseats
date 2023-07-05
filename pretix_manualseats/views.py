import typing
from typing import Any, Dict

from django import forms
from django.contrib import messages
from django.db import transaction
from django.forms.forms import BaseForm
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, FormView, ListView, UpdateView
from pretix.base.forms import I18nModelForm
from pretix.base.models import (
    Event,
    Item,
    OrderPosition,
    Seat,
    SeatCategoryMapping,
    SeatingPlan,
)
from pretix.base.services.seating import generate_seats
from pretix.control.permissions import (
    EventPermissionRequiredMixin,
    OrganizerPermissionRequiredMixin,
)
from pretix.helpers.compat import CompatDeleteView
from pretix.helpers.models import modelcopy


class EventSeatingPlanSetForm(forms.Form):
    seatingplan = forms.ChoiceField(required=False, label=_("Seating Plan"))
    advanced = forms.BooleanField(label=_("Advanced Settings"), required=False)
    users_edit_seatingplan = forms.BooleanField(
        label=_("Customers can choose their own seats"),
        widget=forms.CheckboxInput(attrs={"data-display-dependency": "#id_advanced"}),
        help_text=_(
            "If disabled, you will need to manually assign seats in the backend. "
            "Note that this can mean people will not know their seat after their purchase and it might not be written on their ticket."
        ),
        required=False,
    )

    class Meta:
        fields = ["users_edit_seatingplan", "seatingplan"]


class EventIndex(EventPermissionRequiredMixin, FormView):
    model = SeatingPlan
    template_name = "pretix_manualseats/event/index.html"
    permission = "can_change_orders"
    form_class = EventSeatingPlanSetForm

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_manualseats:index",
            kwargs={
                "organizer": self.get_event().organizer.slug,
                "event": self.get_event().slug,
            },
        )

    def get_seatingplans(self):
        return SeatingPlan.objects.filter(organizer=self.request.organizer)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seatingplans"] = self.get_seatingplans()

        return ctx

    def get_event(self) -> Event:
        return self.request.event

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        event = self.get_event()
        initial["seatingplan"] = event.seating_plan.id if event.seating_plan else "None"
        initial["users_edit_seatingplan"] = event.settings.seating_choice

        return initial

    def get_form(self, form_class=None) -> BaseForm:
        form = typing.cast(EventSeatingPlanSetForm, super().get_form(form_class))
        form.fields["seatingplan"].choices = [(None, "None")] + [
            (i.id, i.name) for i in self.get_seatingplans()
        ]

        return form

    def form_valid(self, form):
        seatingplan_id = form.cleaned_data["seatingplan"]

        event = self.get_event()
        if seatingplan_id:
            event.seating_plan = SeatingPlan.objects.get(id=seatingplan_id)
            event.settings.seating_choice = form.cleaned_data["users_edit_seatingplan"]
        else:
            if event.seating_plan:
                event.seating_plan = None

        event.save()

        if event.seating_plan:
            generate_seats(event, None, event.seating_plan, dict(), None)
        else:
            SeatCategoryMapping.objects.filter(event=event).delete()
            Seat.objects.filter(event=event).delete()

        messages.success(self.request, _("Your changes have been saved."))

        return super().form_valid(form)


class EventMappingForm(forms.Form):
    pass


class EventMapping(EventPermissionRequiredMixin, FormView):
    template_name = "pretix_manualseats/event/mapping.html"
    permission = "can_change_orders"
    form_class = EventMappingForm

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_manualseats:mapping",
            kwargs={
                "organizer": self.get_event().organizer.slug,
                "event": self.get_event().slug,
            },
        )

    def get_seatingplans(self):
        return SeatingPlan.objects.filter(organizer=self.request.organizer)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seatingplan"] = self.get_seating_plan()
        if self.get_seating_plan():
            ctx["seatingcats"] = [
                c.name for c in self.get_seating_plan().get_categories()
            ]
        ctx["items"] = self.get_event().items.all()

        return ctx

    def get_event(self) -> Event:
        return self.request.event

    def get_seating_plan(self) -> Event:
        return self.get_event().seating_plan

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        event = self.get_event()

        if self.get_seating_plan():
            for cat in self.get_seating_plan().get_categories():
                mapping = SeatCategoryMapping.objects.filter(
                    event=event, layout_category=cat.name
                ).first()
                if mapping:
                    initial[f"cat-{cat.name}"] = mapping.product.id

        return initial

    def get_form(self, form_class=None) -> BaseForm:
        form = typing.cast(EventSeatingPlanSetForm, super().get_form(form_class))

        if self.get_seating_plan():
            for cat in self.get_seating_plan().get_categories():
                form.fields[f"cat-{cat.name}"] = forms.ChoiceField(
                    label=cat.name,
                    choices=[(i.id, i.name) for i in self.get_event().items.all()]
                    + [(None, "None")],
                    required=False,
                )
        return form

    def form_valid(self, form: BaseForm) -> HttpResponse:
        event = self.get_event()
        SeatCategoryMapping.objects.filter(event=event).delete()

        if self.get_seating_plan():
            for cat in self.get_seating_plan().get_categories():
                if form.cleaned_data[f"cat-{cat.name}"]:
                    product = Item.objects.filter(
                        id=form.cleaned_data[f"cat-{cat.name}"]
                    ).first()
                    queryset = SeatCategoryMapping.objects.create(
                        event=event, layout_category=cat.name, product=product
                    )
                    queryset.save()

        messages.success(self.request, _("Your changes have been saved."))

        return super().form_valid(form)


class EventImportForm(forms.Form):
    data = forms.CharField(
        widget=forms.Textarea(),
        label="Raw Data",
        help_text="header should equal: seat_guid,orderposition_secret",
        required=False,
    )

    pass


class EventImport(EventPermissionRequiredMixin, FormView):
    template_name = "pretix_manualseats/event/import.html"
    permission = "can_change_orders"
    form_class = EventImportForm

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_manualseats:import",
            kwargs={
                "organizer": self.get_event().organizer.slug,
                "event": self.get_event().slug,
            },
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seatingplan"] = self.get_seating_plan()
        if self.get_seating_plan():
            ctx["seatingcats"] = [
                c.name for c in self.get_seating_plan().get_categories()
            ]
        ctx["items"] = self.get_event().items.all()
        ctx["seats"] = Seat.objects.filter(event=self.get_event())
        ctx["seatscsv"] = "seat_guid\n" + "\n".join(
            [seat.seat_guid for seat in Seat.objects.filter(event=self.get_event())]
        )
        ctx["orderpositionscsv"] = "orderposition_secret\n" + "\n".join(
            [
                pos.secret
                for pos in OrderPosition.objects.filter(order__event=self.get_event())
            ]
        )

        return ctx

    def get_event(self) -> Event:
        return self.request.event

    def get_seating_plan(self) -> Event:
        return self.get_event().seating_plan

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()

        return initial

    def form_valid(self, form: BaseForm) -> HttpResponse:
        event = self.get_event()

        if not event.seating_plan:
            messages.error(self.request, _("No seating plan"))
            return super().form_invalid(form)

        data = typing.cast(str, form.cleaned_data["data"])
        lines = data.split("\n")
        lines = [line.strip() for line in lines]

        if len(lines) <= 1:
            OrderPosition.objects.filter(order__event=event).update(seat=None)
            messages.success(self.request, _("Removed all seat assignments"))
            return super().form_valid(form)

        if not (lines[0].startswith("seat_guid,orderposition_secret")):
            messages.error(self.request, _("Invalid Format"))
            return super().form_invalid(form)

        for line in lines[1:]:
            (seat_guid, orderposition_secret) = [
                line.strip() for line in line.split(",")
            ]
            order = OrderPosition.objects.filter(secret=orderposition_secret).first()
            seat = Seat.objects.filter(seat_guid=seat_guid).first()
            if not order:
                messages.error(
                    self.request, _(f"Unable to match order ({orderposition_secret})")
                )
                return super().form_invalid(form)
            if not seat:
                messages.error(self.request, _(f"Unable to match seat ({seat_guid})"))
                return super().form_invalid(form)

            order.seat = seat
            order.save()

        messages.success(self.request, _("Your changes have been saved."))

        return super().form_valid(form)


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
