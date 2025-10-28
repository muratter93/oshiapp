from django.conf import settings
from money.models import Wallet
 
def navbar(request):
    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(member=request.user).first()
        return {
            "user": request.user,
            "wallet": wallet,
        }
    return {}