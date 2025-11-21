from django.contrib import admin
from .models import Gift, GiftImage

# ------------------------
# GiftImage（サブ画像）をインラインで編集
# ------------------------
class GiftImageInline(admin.TabularInline):
    model = GiftImage
    extra = 1
    fields = ("image", "caption", "display_order")
    ordering = ("display_order",)


# ------------------------
# Gift（返礼品）管理画面
# ------------------------
@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ("title", "zoo", "price", "created_at")
    list_filter = ("zoo",)
    search_fields = ("title", "description")
    
    inlines = [GiftImageInline]

    fieldsets = (
        ("基本情報", {
            "fields": ("zoo", "title", "description", "price")
        }),
        ("メイン画像", {
            "fields": ("main_image",)
        }),
    )


# ------------------------
# GiftImage（サブ画像）単体を見たいとき用（必要なら）
# ------------------------
@admin.register(GiftImage)
class GiftImageAdmin(admin.ModelAdmin):
    list_display = ("gift", "display_order")
    list_filter = ("gift",)
    ordering = ("gift", "display_order")
