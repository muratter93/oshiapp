from django.contrib import admin
from .models import Donation
# ハンコ
from django.contrib import admin
from .models import Stamp

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("donor", "zoo", "amount", "created_at")
    list_filter = ("zoo", "created_at")
    search_fields = ("donor__username", "zoo__zoo_name")



# ハンコ
@admin.register(Stamp)
class StampAdmin(admin.ModelAdmin):
    list_display = ("zoo", "name", "is_active")
    list_filter = ("zoo",)
    list_editable = ("is_active",)