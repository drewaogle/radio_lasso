from django.urls import path

from . import views

app_name = "tuner"
urlpatterns = [
        path("",views.index, name="index"),
        path("main",views.main, name="main"),
        path("tune",views.tune, name="tune"),
        ]
