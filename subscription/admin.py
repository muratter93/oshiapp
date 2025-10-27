from django.contrib import admin
from .models import SubscribePlan
from .models import SubMember

@admin.register(SubscribePlan)
class SubscribePlanAdmin(admin.ModelAdmin):
    list_display = ("code", "plan_name", "amount", "st_point")
    search_fields = ("code", "plan_name")
    ordering = ("code",)

@admin.register(SubMember)
class SubMemberAdmin(admin.ModelAdmin):
    list_display = ("sub_member_id", "member", "plan", "sub", "sing_up", "end_day", "sing_mon")
    list_display_links = ("sub_member_id", "member")
    list_filter = ("sub", "plan__code")
    search_fields = ("member__username", "plan__code")