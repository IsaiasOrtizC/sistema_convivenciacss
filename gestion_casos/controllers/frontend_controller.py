from django.shortcuts import render


def react_app_view(request):
    return render(request, 'gestion_casos/react_app.html')
