from django.urls import path
from . import views

from .views import reset_donations

app_name = "donation"

urlpatterns = [
    path("", views.donate, name="donate"),
    path("confirm/", views.donate_confirm, name="donate_confirm"),
    path("complete/<int:donation_id>/", views.donate_complete, name="donate_complete"),
    path("receipt/<int:donation_id>/", views.donation_receipt_pdf, name="donation_receipt_pdf"),
    path("history/", views.donation_history, name="donation_history"), 

    path('admin/reset_donations/', reset_donations, name='reset_donations'),  # ←バルス
]
