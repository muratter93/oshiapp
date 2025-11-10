from django.contrib import admin
from .models import Animal, Zoo, Picture

class PictureInline(admin.TabularInline):
    model = Picture
    extra = 0
    fields = ("image_url", "caption", "credit", "display_order", "is_primary")
    ordering = ("display_order",)

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
  list_display = ("animal_id", "japanese", "name", "sex", "total_point")
  list_display_links = ("animal_id", "japanese", "name")
  list_filter = ("sex", "generic", "specific")
  search_fields = ("japanese", "scientific", "name", "generic", "specific")
  list_per_page = 20
  inlines = [PictureInline]   # ← ここを足すと編集画面でURL画像を編集可

@admin.register(Zoo)
class ZooAdmin(admin.ModelAdmin):
    list_display = ("zoo_id", "zoo_no", "zoo_name", "zoo_created_at")
    search_fields = ("zoo_no", "zoo_name")
    list_per_page = 20
    fields = ("zoo_no", "zoo_name")
    readonly_fields = ("zoo_no",)  # 手入力させたくない場合だけ

@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ("pic_id", "animal", "display_order", "is_primary", "image_url", "pic_created_at")
    list_filter = ("is_primary",)
    search_fields = ("image_url",)
    ordering = ("animal", "display_order")
    list_select_related = ("animal",)  # N+1対策

    @admin.display(description="動物")
    def animal_label(self, obj):
        # __str__が長い/見にくい場合は好みで整形
        return f"{obj.animal.japanese}（{obj.animal.name}）"