from django.shortcuts import render

def about_in(request):
    return render(request, "pages/about.html")

def structure(request):
    return render(request, "pages/structure.html")