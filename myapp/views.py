from django.shortcuts import render
from django.http import HttpResponse

def home_view(request):
    return render(request, 'home.html')
    #return HttpResponse("<h1>Home page</h1>")

    #context = {'title': 'Welcome'}
    #if request.user.is_authenticated:
    #    context['username'] = request.user.username
    #return render(request, 'home.html', context)