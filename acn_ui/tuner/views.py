from django.shortcuts import render

from django.http import HttpResponse,JsonResponse
from django.views.decorators.http import require_POST

from tuner.submitter import submit_audio_cmd
# Create your views here.

def index(request):
    return HttpResponse("Ohaiyo Gozaimasu World")

def main(request):
    return render(request, "tuner/remote.html")

@require_POST
def tune(request):
    print("Tune request for channel : " + request.POST.get('channel'))
    submit_audio_cmd("channel",request.POST.get('channel'))
    return JsonResponse({'action':'sent'})
