from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect

from .models import Member
from animals.models import Zoo


class MemberAdminForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        is_keeper = cleaned.get("is_keeper")
        zoo = cleaned.get("zoo")
        if is_keeper and not zoo:
            raise ValidationError({"zoo": "飼育員にする場合は『所属動物園』を選択してください。"})
        return cleaned

@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member
    form = MemberAdminForm

    list_display = (
        "id", "username", "email", "name", "birth",
        "is_superuser", "is_staff", "is_keeper", "zoo",
        "is_active", "last_login",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "is_keeper", "zoo")
    search_fields = ("username", "email", "name")
    ordering = ("id",)
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {
            "fields": ("username", "email", "password")  
        }),
        ("個人情報", {
            "fields": ("name", "birth", "postal_code", "address", "phone")
        }),
        ("飼育員", {
            "fields": ("is_keeper", "zoo"),
            "description": "飼育員にする場合は所属動物園を必ず選択してください。"
        }),
        ("権限", {
            "fields": ("is_active",),
        }),
        ("日付", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
        ("個人情報", {
            "classes": ("wide",),
            "fields": ("name", "birth", "postal_code", "address", "phone"),
        }),
        ("飼育員", {
            "classes": ("wide",),
            "fields": ("is_keeper", "zoo"),
        }),
        ("権限", {
            "classes": ("wide",),
            "fields": ("is_active", "is_staff", ),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        if obj and obj.is_superuser:
            new_fieldsets = []
            for name, opts in fieldsets:
                fields = list(opts.get("fields", ()))
                if name is None or name == "" or name == "": 
                    if "password" in fields:
                        fields.remove("password")
                new_fieldsets.append((name, {**opts, "fields": tuple(fields)}))
            return tuple(new_fieldsets)

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and not obj.is_keeper:
            if "zoo" in form.base_fields:
                form.base_fields["zoo"].disabled = True
        return form

    def user_change_password(self, request, id, form_url=""):
        target_user = get_object_or_404(self.model, pk=id)
        if target_user.is_superuser:
            messages.error(request, "このユーザーのパスワードはリセットできません。")
            return redirect("admin:accounts_member_change", target_user.pk)
        return super().user_change_password(request, id, form_url)
