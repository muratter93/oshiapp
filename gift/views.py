from django.shortcuts import render, get_object_or_404
from .models import Gift

def gift_list(request):
    gifts = Gift.objects.select_related("zoo").all().order_by("-created_at")
    return render(request, "gifts/gift_list.html", {"gifts": gifts})

def gift_detail(request, pk):
    gift = get_object_or_404(Gift, pk=pk)
    images = gift.images.all()  # related_name="images"
    return render(request, "gifts/gift_detail.html", {
        "gift": gift,
        "images": images,
    })
