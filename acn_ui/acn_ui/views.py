from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseNotFound

class custom404middleware:
    def __init__(self,get_response):
        self.get_response = get_response
    def __call__(self,request):
        response = self.get_response(request)
        if response.status_code == 404:
            if request.user.is_authenticated:
                response = redirect(reverse("tuner:main"))
            else:
                response = redirect(reverse("login"))
        return response

