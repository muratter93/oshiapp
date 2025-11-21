# animals/admin.py
from datetime import date

from django import forms
from django.contrib import admin
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce

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

    # 一覧に出すカラム
    list_display = (
        "zoo_name",

        # --- 推しポイント ---
        "total_point_sum_display",
        "last_paid_point_sum_display",
        "unpaid_points_display",
        "unpaid_point_coins_display",
        "last_paid_at",

        # --- サブスク ---
        "sub_unpaid_amount_display",   # 今回支援分
        "last_paid_sub_total_display", # 累計支援額
        "last_paid_sub_at",            # 日時
    )

    search_fields = ("zoo_no", "zoo_name")
    list_per_page = 20

    # 編集画面
    fields = (
        "zoo_no",
        "zoo_name",
        "zoo_postcode",
        "zoo_address",
        "zoo_phone",

        # 推しポイント
        "last_paid_point_sum",
        "last_paid_at",

        # サブスク
        "last_paid_sub_total",
        "sub_unpaid_amount",
        "last_paid_sub_at",
    )

    readonly_fields = (
        "zoo_no",
        "last_paid_point_sum",
        "last_paid_at",
        "last_paid_sub_total",   # 累計
        "sub_unpaid_amount",     # 未支援額
        "last_paid_sub_at",
    )

    # ------- 集計（推しポイントだけ必要） -------
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # ★ 動物ポイント合計（ポイント方式はそのまま）
        qs = qs.annotate(
            _total_point_sum=Coalesce(Sum("animals__total_point"), 0),
        )

        return qs

    # ------- 表示用：推しポイント -------
    @admin.display(description="累計推しポイント")
    def total_point_sum_display(self, obj):
        return f"{obj._total_point_sum:,}"

    @admin.display(description="前回推しポイント")
    def last_paid_point_sum_display(self, obj):
        return f"{obj.last_paid_point_sum:,}"

    @admin.display(description="今回推しポイント")
    def unpaid_points_display(self, obj):
        unpaid = max(obj._total_point_sum - obj.last_paid_point_sum, 0)
        return f"{unpaid:,}"

    @admin.display(description="今回支援金額(ポイント)")
    def unpaid_point_coins_display(self, obj):
        unpaid = max(obj._total_point_sum - obj.last_paid_point_sum, 0)
        return f"{unpaid * 100:,} 円"

    # ------- 表示用：サブスク（新ロジック） -------
    @admin.display(description="今回サブスク支援額")
    def sub_unpaid_amount_display(self, obj):
        return f"{obj.sub_unpaid_amount:,}"

    @admin.display(description="累計サブスク支援額")
    def last_paid_sub_total_display(self, obj):
        return f"{obj.last_paid_sub_total:,}"





@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ("pic_id", "animal", "display_order", "is_primary", "image_url", "pic_created_at")
    list_filter = ("is_primary", "animal")
    search_fields = ("image_url", "caption", "credit", "animal__japanese", "animal__name")
    ordering = ("animal", "display_order")
    list_select_related = ("animal",)
    raw_id_fields = ("animal",)
