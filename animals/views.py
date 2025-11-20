from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Animal

# ---- 詳細ページ ----
def detail(request, animal_id):
    animal = get_object_or_404(Animal, animal_id=animal_id)
    return render(request, "animals/detail.html", {"animal": animal})


# ---- ランキングページ ----
def ranking(request):
    animals = Animal.objects.order_by('-total_point')
    return render(request, "animals/ranking.html", {"animals": animals})


# ---- 推しP を +1 するAPI ----
@require_POST
def push_animal(request, animal_id):
    animal = get_object_or_404(Animal, animal_id=animal_id)
    animal.total_point += 1
    animal.save()

    return JsonResponse({
        "success": True,
        "total_point": animal.total_point
    })
