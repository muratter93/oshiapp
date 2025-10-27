from django.contrib import admin
from .models import SubscribePlan

@admin.register(SubscribePlan)
class SubscribePlanAdmin(admin.ModelAdmin):
    list_display = ("code", "plan_name", "amount", "st_point")
    search_fields = ("code", "plan_name")
    ordering = ("code",)