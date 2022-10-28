
import code
from django.http import (
   HttpResponse
)

from django.utils.translation import gettext_lazy as _

import json
from base64 import b64encode

from pretix.base.models import ( SeatingPlan,Seat,Item )
from pretix.api.serializers.organizer import (
    SeatingPlanSerializer
)

from django.contrib.auth.models import User
from rest_framework import viewsets
from django.shortcuts import redirect

def retrieve(request, **kwargs):
        
        if 'subevent' in kwargs and request.event.has_subevents :
            seats = [ seat.seat_guid for seat in Seat.objects.filter(subevent=kwargs['subevent']) if not seat.is_available() ]
            queryset = SeatingPlan.objects.filter(organizer=request.event.organizer,subevents=kwargs['subevent'])[0]
        else :
            seats = [ seat.seat_guid for seat in Seat.objects.filter(event= request.event) if not seat.is_available()]
            queryset = SeatingPlan.objects.filter(organizer=request.event.organizer,events=request.event)[0]
        serializer = SeatingPlanSerializer(queryset,many=False)
        final_data = {'seating_plan':serializer.data ,'seats':seats}
        return HttpResponse(json.dumps(final_data),content_type="application/json")
    
def seat_product_assign(request, **kwargs):
        if 'item' in request.GET and 'seat_guid' in request.GET:
            parts = request.GET['item'].split("_")
            if not 'subevent' in kwargs:
                seat = Seat.objects.get(event=request.event,seat_guid=request.GET['seat_guid'])
                seat.product = Item.objects.get(id=int(parts[1]))
                seat.save()
            else :
                seat = Seat.objects.get(subevent_id=kwargs['subevent'],event=request.event,seat_guid=request.GET['seat_guid'])
                seat.product = Item.objects.get(id=int(parts[1]))
                seat.save()
        else :
            return HttpResponse(content="check your parameters")
        return HttpResponse(content="success")




        