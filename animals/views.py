from django.shortcuts import render

def detail(request, pk: int):
    return render(request, "animals/detail.html", {
        # "animal": animal,
    })

