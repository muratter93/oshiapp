from django.urls import path
from . import views

app_name = "donation"

urlpatterns = [
    path("", views.donate, name="donate"),
    path("confirm/", views.donate_confirm, name="donate_confirm"),
    path("complete/<int:donation_id>/", views.donate_complete, name="donate_complete"),
    path("receipt/<int:donation_id>/", views.donation_receipt_pdf, name="donation_receipt_pdf"),
    path("history/", views.donation_history, name="donation_history"),  # ←追加
]
