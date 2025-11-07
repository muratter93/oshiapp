from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from animals.models import Animal

def ranking(request):
    all_animals = Animal.objects.all().order_by('-total_point')
    other_animals = all_animals[20:]
    
    #21位以降に1ページずつに表示される動物の数↓
    paginator = Paginator(other_animals, 30)
    total_pages = paginator.num_pages + 1

    page_number_str = request.GET.get('page', '1')
    try:
        page_number = int(page_number_str)
    except ValueError:
        page_number = 1

    if page_number < 1:
        page_number = 1
    elif page_number > total_pages:
        page_number = total_pages

    context = {
        'paginator': paginator,
        'actual_page_num': page_number,
        'total_pages': total_pages,
    }

    window = 2 
    page_range = []

    if total_pages > 1:
        
        page_range.append(1)

        if page_number > 1 + window + 1:
            page_range.append('...') 

        start = max(2, page_number - window)
        end = min(total_pages - 1, page_number + window)
        
        for i in range(start, end + 1):
            if i not in page_range:
                page_range.append(i)

        if page_number < total_pages - window - 1:
            page_range.append('...') 

        if total_pages not in page_range:
            page_range.append(total_pages)
    
    context['page_range'] = page_range

    if page_number == 1:
        context['animals'] = all_animals[:20]
        context['is_page_1'] = True
        try:
            context['page_obj'] = paginator.get_page(1)
        except EmptyPage:
            # 21位以降の動物がいない場合
            context['page_obj'] = None
    else:
        page_num_for_paginator = page_number - 1
        
        try:
            page_obj = paginator.get_page(page_num_for_paginator)
        except EmptyPage:
            page_obj = None 

        context['page_obj'] = page_obj
        context['is_page_1'] = False
        
        if page_obj:
            context['start_rank'] = 20 + page_obj.start_index()
        else:
            context['start_rank'] = 21 
            
    return render(request, 'ranking/ranking.html', context)