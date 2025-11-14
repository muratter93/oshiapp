# animals/admin.py
from datetime import date

from django import forms
from django.contrib import admin

from .models import Animal, Zoo, Picture


class AnimalAdminForm(forms.ModelForm):
    """Animal モデル用の admin フォームカスタマイズ"""

    class Meta:
        model = Animal
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "birth" in self.fields:
            widget = self.fields["birth"].widget
            widget.input_type = "date"                     
            widget.attrs["max"] = date.today().isoformat()

class PictureInline(admin.TabularInline):
    model = Picture
    extra = 0
    fields = ("image_url", "caption", "credit", "display_order", "is_primary")
    ordering = ("display_order",)
    show_change_link = True


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    form = AnimalAdminForm 

    list_display = (
        "animal_id",
        "japanese",
        "name",
        "sex",
        "zoo",
        "total_point",
        "diet_display",
        "is_active",
    )
    list_display_links = ("animal_id", "japanese", "name")

    list_filter = ("sex", "generic", "specific", "zoo", "diet", "is_active")

    search_fields = ("japanese", "scientific", "name", "generic", "specific", "zoo__zoo_name")
    list_per_page = 20
    inlines = [PictureInline]

    readonly_fields = ("generic", "specific", "scientific")

    fieldsets = (
        (None, {
            "fields": ("japanese", "name", "zoo", "sex", "birth", "diet", "txt"),
        }),
        ("画像", {
            "fields": ("pic1",),
        }),
        ("メタ", {
            "fields": ("total_point", "is_active"),
        }),
    )

    @admin.display(description="主食", ordering="diet")
    def diet_display(self, obj):
        return obj.get_diet_display() or "—"


@admin.register(Zoo)
class ZooAdmin(admin.ModelAdmin):
    list_display = ("zoo_id", "zoo_no", "zoo_name", "zoo_postcode", "zoo_address", "zoo_phone", "zoo_created_at")
    search_fields = ("zoo_no", "zoo_name", "zoo_address", "zoo_phone", "zoo_postcode")
    list_per_page = 20
    fields = ("zoo_no", "zoo_name", "zoo_postcode", "zoo_address", "zoo_phone")
    readonly_fields = ("zoo_no",)


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ("pic_id", "animal", "display_order", "is_primary", "image_url", "pic_created_at")
    list_filter = ("is_primary", "animal")
    search_fields = ("image_url", "caption", "credit", "animal__japanese", "animal__name")
    ordering = ("animal", "display_order")
    list_select_related = ("animal",)
    raw_id_fields = ("animal",)
