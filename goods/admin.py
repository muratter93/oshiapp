from django.contrib import admin
from .models import Goods

from django.contrib import admin
from .models import Order, OrderItem

from .models import Goods, Order, OrderItem, CartItem


# --- グッズモデル ---
@admin.register(Goods)
class GoodsAdmin(admin.ModelAdmin):
    list_display = ('name', 'required_stanning_points', 'stock')
    search_fields = ('name',)
    list_filter = ('required_stanning_points',)



# --- 注文アイテムモデル ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('member', 'created_at', 'total_stanning_points', 'is_confirmed')
    search_fields = ('member__username',)
    list_filter = ('is_confirmed', 'created_at')
    inlines = [OrderItemInline]    


# --- 買い物かごモデル ---
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('member', 'goods', 'quantity', 'added_at')
    search_fields = ('member__username', 'goods__name')
    list_filter = ('added_at',)
