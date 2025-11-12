# subscription/admin.py
from django.contrib import admin
from .models import SubscribePlan, SubMember
from django.utils import timezone

@admin.register(SubscribePlan)
class SubscribePlanAdmin(admin.ModelAdmin):
    list_display = ("code", "plan_name", "amount", "st_point")
    search_fields = ("code", "plan_name")
    ordering = ("code",)

@admin.register(SubMember)
class SubMemberAdmin(admin.ModelAdmin):
    list_display = (
        "sub_member_id",
        "member",
        "animal",
        "plan",
        "is_recurring",  # sub -> is_recurring
        "sign_up",       # sing_up -> sign_up
        "end_day",
        "sign_mon",      # sing_mon -> sign_mon
    )
    list_display_links = ("sub_member_id", "member")
    list_filter = ("is_recurring", "plan__code", "animal__japanese")  # sub -> is_recurring
    search_fields = (
        "member__username",
        "member__name",
        "animal__japanese",
        "animal__name",
        "plan__code",
    )
    ordering = ("member__username", "sign_up")
    readonly_fields = ("sign_mon",)
    fieldsets = (
        (None, {"fields": ("member", "plan", "animal", "is_recurring")}),
        ("期間情報", {"fields": ("sign_up", "end_day", "sign_mon")}),
    )

    @admin.action(description="選択した契約を本日で終了にする")
    def close_today(self, request, queryset):
        today = timezone.localdate()
        updated = queryset.update(end_day=today)
        self.message_user(request, f"{updated} 件を終了日に更新しました。")

    actions = ["close_today"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("member", "animal", "plan")
