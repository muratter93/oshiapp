from django.contrib import admin
from .models import Donation

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("donor", "zoo", "amount", "created_at")
    list_filter = ("zoo", "created_at")
    search_fields = ("donor__username", "zoo__zoo_name")
