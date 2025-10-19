from django.shortcuts import render

def charge(request):
    return render(request, "money/charge.html")