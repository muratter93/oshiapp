from django.shortcuts import get_object_or_404, render
from .models import Animal

def detail(request, pk: int):
    animal = get_object_or_404(Animal, pk=pk)
    return render(request, "animals/detail.html", {"animal": animal})