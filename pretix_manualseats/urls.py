from django.urls import path

from . import views

urlpatterns = [
    path(
        "control/event/<str:organizer>/<str:event>/manualseats/",
        views.EventIndex.as_view(),
        name="index",
    ),
    path(
        "control/event/<str:organizer>/<str:event>/manualseats/mapping/",
        views.EventMapping.as_view(),
        name="mapping",
    ),
    path(
        "control/event/<str:organizer>/<str:event>/manualseats/assign/",
        views.EventAssign.as_view(),
        name="assign",
    ),
    path(
        "control/organizer/<str:organizer>/manualseats/",
        views.OrganizerSeatingPlanList.as_view(),
        name="index",
    ),
    path(
        "control/organizer/<str:organizer>/manualseats/add",
        views.OrganizerPlanAdd.as_view(),
        name="add",
    ),
    path(
        "control/organizer/<str:organizer>/manualseats/<int:seatingplan>/edit",
        views.OrganizerPlanEdit.as_view(),
        name="edit",
    ),
    path(
        "control/organizer/<str:organizer>/manualseats/<int:seatingplan>/delete",
        views.OrganizerPlanDelete.as_view(),
        name="delete",
    ),
]
