from django.urls import path

from . import views

app_name = "tuner"
urlpatterns = [
        path("",views.index, name="index"),
        path("main",views.main, name="main"),
        path("playlist",views.player_playlist, name="playlist"),
        path("control",views.player_control, name="control"),
        ]
