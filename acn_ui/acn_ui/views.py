from django.shortcuts import redirect
from django.urls import reverse

def handle404(request,exception):
    return redirect(reverse("login"))
