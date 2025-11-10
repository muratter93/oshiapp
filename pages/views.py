from django.shortcuts import render

def about(request):
    return render(request, "pages/about.html")

def about_in(request):
    return render(request, "pages/about_in.html")

def structure(request):
    return render(request, "pages/structure.html")