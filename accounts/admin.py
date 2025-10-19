from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import get_object_or_404, redirect
from .models import Member

@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member

    list_display = ("id", "username", "email", "name")

    search_fields = ("email", "name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("個人情報", {"fields": ("name", "postal_code", "address", "phone")}),
        ("日付", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    # superuserのパスワード変更不可
    def user_change_password(self, request, id, form_url=""):
        target_user = get_object_or_404(self.model, pk=id)

        if target_user.is_superuser:
            messages.error(
                request,
                "このユーザーのパスワードはリセットできません。"
            )
            return redirect("admin:accounts_member_change", target_user.pk)

        return super().user_change_password(request, id, form_url)