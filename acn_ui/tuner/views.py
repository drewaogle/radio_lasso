from django.shortcuts import render

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
    playlists = [ 
                PlaylistItem(name="baby", for_user="Baby"),
                PlaylistItem(name="teen", for_user="Teen")
                ]
    player_controls = [
               TunerControl(name="play",emoji="#x23f5;"),
               TunerControl(name="pause",emoji="#x23f8;"),
               TunerControl(name="stop",emoji="#x23f9;")
               ]
    context = { "playlists" : playlists , "controls":player_controls }
    return render(request, "tuner/remote.html",context)

@require_POST
def player_playlist(request):
    print("Tune request for playlist : " + request.POST.get('channel'))
    submit_audio_cmd("channel",request.POST.get('channel'))
    return JsonResponse({'action':'sent'})

@require_POST
def player_control(request):
    print("Tune request for control : " + request.POST.get('control'))
    submit_audio_cmd("X",request.POST.get('control'))
    return JsonResponse({'action':'sent'})
