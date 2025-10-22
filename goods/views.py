# views.py
from django.shortcuts import render
from .models import Goods

def goods_list_view(request):
    goods_list = Goods.objects.all()
    return render(request, 'goods/goods_list.html', {'goods_list': goods_list})



from django.shortcuts import render

def charge(request):
    return render(request, 'goods/goods_list.html')
