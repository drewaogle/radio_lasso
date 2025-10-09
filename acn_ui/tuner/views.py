from django.shortcuts import render,redirect
from django.urls import reverse

from django.http import HttpResponse,JsonResponse
from django.views.decorators.http import require_POST

from tuner.submitter import submit_audio_cmd
from pydantic import BaseModel
# Create your views here.

def index(request):
    return HttpResponse("Ohaiyo Gozaimasu World")

class TunerControl(BaseModel):
    name: str
    emoji: str

class PlaylistItem(BaseModel):
    name:str
    for_user:str

def main(request):
    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    playlists = [ 
                PlaylistItem(name="baby", for_user="Baby"),
                PlaylistItem(name="teen", for_user="Teen")
                ]
    player_controls = [
               TunerControl(name="play",emoji="play-btn"),
               TunerControl(name="pause",emoji="pause-btn"),
               TunerControl(name="stop",emoji="stop-btn"),
               ]
    context = { "playlists" : playlists , "controls":player_controls }
    return render(request, "tuner/remote.html",context)

@require_POST
def player_playlist(request):
    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    channel =  request.POST.get('channel')
    print(f"Tune request for playlist : {channel} ")
    submit_audio_cmd("playlist", channel )
    if ok:
        context[ "response"] =  f"Changed to {channel}"  
    else:
        context[ "response"] =  f"Unable to change to {channel}" 
    resp = render(request, "tuner/response.html", context )
    resp.headers["HX-Trigger-After-Swap"] = "toasts:initialize"
    return resp 

@require_POST
def player_control(request):
    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    pctl =  request.POST.get('control')
    print(f"Tune request for control : {pctl}") 
    ok = False
    context = {}
    ok = submit_audio_cmd("player", pctl ) 

    if ok:
        context[ "response"] =  f"Sent {pctl}"  
    else:
        context[ "response"] =  f"Unable to send {pctl}" 
    resp = render(request, "tuner/response.html", context )
    resp.headers["HX-Trigger-After-Swap"] = "toasts:initialize"
    return resp
