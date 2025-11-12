# animals/admin.py
from django.contrib import admin
from .models import Animal, Zoo, Picture

class PictureInline(admin.TabularInline):
    model = Picture
    extra = 0
    fields = ("image_url", "caption", "credit", "display_order", "is_primary")
    ordering = ("display_order",)
    show_change_link = True

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("animal_id", "japanese", "name", "sex", "zoo", "total_point")
    list_display_links = ("animal_id", "japanese", "name")
    list_filter = ("sex", "generic", "specific", "zoo")
    search_fields = ("japanese", "scientific", "name", "generic", "specific", "zoo__zoo_name")
    list_per_page = 20
    inlines = [PictureInline]

    # ★ ここがポイント：非編集フィールドを readonly_fields に入れる
    readonly_fields = ("generic", "specific", "scientific")

    fieldsets = (
        (None, {
            "fields": ("japanese", "name", "zoo", "sex", "birth", "txt"),
        }),
        # ("学術情報", {
        #     # readonly_fields に入れてあれば fields に並べてOK
        #     "fields": ("generic", "specific", "scientific"),
        #     "classes": ("collapse",),
        # }),
        ("画像", {
            "fields": ("pic1",),
            # "classes": ("collapse",),
        }),
        ("メタ", {
            "fields": ("total_point",),
        }),
    )

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
