from django.contrib import admin
from .models import Wallet, CheerCoinPurchase

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('member', 'cheer_coin_balance', 'stanning_point_balance')
    search_fields = ('member__username',)

# チアコイン購入履歴    
@admin.register(CheerCoinPurchase)
class CheerCoinPurchaseAdmin(admin.ModelAdmin):
    list_display = ('member', 'coins', 'price', 'purchased_at')
    list_filter = ('purchased_at',)
    search_fields = ('member__username',)