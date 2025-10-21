from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('member', 'cheer_coin_balance', 'stanning_point_balance')
    search_fields = ('member__username',)
    
