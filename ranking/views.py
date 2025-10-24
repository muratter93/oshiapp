# from django.shortcuts import render
# from animals.models import Animal

# def ranking(request):

#     animals = Animal.objects.all().order_by('-total_point')

#     return render(request, "ranking/ranking.html", {'animals' : animals})

from django.shortcuts import render
from animals.models import Animal
 
def ranking(request):
    animals = Animal.objects.all().order_by('-total_point')
    return render(request, 'ranking/ranking.html', {'animals': animals})