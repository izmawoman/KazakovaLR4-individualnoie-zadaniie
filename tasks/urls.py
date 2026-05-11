from django.urls import path
from . import views

urlpatterns = [
    path("", views.identify_view, name="identify"),
    path("pin/", views.pin_view, name="pin"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logs/", views.logs_view, name="logs"),
    path("logout/", views.logout_view, name="logout"),
    path("reset-entry/", views.reset_entry_view, name="reset_entry"),
]