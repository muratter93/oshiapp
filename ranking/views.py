from django.core.paginator import Paginator
from django.shortcuts import render
from animals.models import Animal

def ranking(request):
    animals = Animal.objects.all().order_by('-total_point')

    top_20 = animals[:20]

    paginator = Paginator(animals[20:], 40)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'animals': top_20,
        'page_obj': page_obj
    }
    return render(request, 'ranking/ranking.html', context)

