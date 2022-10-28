from asyncio import events
import io
from msilib.schema import Error
import sys
from multiprocessing import Event
from re import template
from sre_parse import CATEGORIES
from typing import Mapping
from unicodedata import category

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Sum
from .seatingForm import SeatingForm
from django.http import (
    Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect,
    JsonResponse,HttpRequest
)
from pretix.control.permissions import EventPermissionRequiredMixin

from django.shortcuts import redirect, render
from django.urls import resolve, reverse
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from pretix.multidomain.urlreverse import eventreverse


import json
from base64 import b64encode
from django.views.generic import (
    FormView,ListView
)
import requests
import pprint
from pretix.base.models import ( SeatingPlan , SeatCategoryMapping,Item, Seat,SubEvent)

from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework import viewsets
from rest_framework import serializers
from django.shortcuts import redirect
from pretix.api.views.organizer import  SeatingPlanViewSet,TeamAPITokenViewSet,TeamViewSet,TeamMemberViewSet
from pretix.api.views.event import EventViewSet
from pretix.api.serializers.organizer import (
    SeatingPlanSerializer
)
from pretix.base.models import (
    SeatingPlan,Seat
)
from pretix.base.services.seating import (
    generate_seats
)

from pretix.api.serializers.event import (
    EventSerializer,

)


def DisplaySeriesTable(request,**kwargs):
    if not request.event.has_subevents:
        return redirect(reverse('plugins:seating_plan:event.seating.display',kwargs={
            'event':request.event.slug,
            'organizer':request.organizer.slug
        }))
    subevents = request.event.subevents.all()
    return render(request,'seating_plan/subevents.html',{'subevents':subevents})



# displaying the seating plan and setting the seatcategory mapping
def  DisplaySeating(request,**kwargs):
    
    object_methods = [method_name for method_name in dir(request.session)
                  ]
    print(object_methods, type(object_methods))
    if ( 'subevent' in request.GET ) and request.event.has_subevents :
            subevent = request.GET['subevent']
            subevent_ob = SubEvent.objects.filter(id=subevent)[0]
    else :
        subevent_ob = None
    if (request.method == 'POST'):
        if subevent_ob is not None :
            maps = SeatCategoryMapping.objects.filter(event=request.event)
        else :
            maps = SeatCategoryMapping.objects.filter( event = request.event, subevent=subevent_ob)
        print(maps)
        if maps is not None:
            maps.delete()
            
            
        items_cats = list(request.POST.keys())[1:]
        print(items_cats)
        for item_cat in items_cats:
            item_name , cat = item_cat.split('_____')
            iteml = Item.objects.filter(event_id = request.event.id)
            itemn = [ itemll for itemll in iteml if str(itemll.name) == item_name][0]
            if ( 'subevent' in request.GET ) and request.event.has_subevents :
                queryset = SeatCategoryMapping.objects.create(event=request.event, subevent = subevent_ob , layout_category = cat,  product = itemn)
            else :
                queryset = SeatCategoryMapping.objects.create( event = request.event , layout_category = cat,  product = itemn)
            queryset.save()
            
    if ( 'subevent' in request.GET ) and request.event.has_subevents :
      
        categories = SeatingPlan.objects.filter(organizer=request.event.organizer,subevents=subevent)[0].layout_data['categories']
    else :
        seating_plans  = SeatingPlan.objects.filter(organizer=request.event.organizer,events=request.event)
        if len(seating_plans) > 0 :
            categories = seating_plans[0].layout_data['categories']
        else : 
           return  redirect(reverse('plugins:seating_plan:event.seating.subevents', kwargs={
            'event': request.event.slug,
            'organizer': request.event.organizer.slug}
                             ))
    items = Item.objects.filter(event_id = request.event.id)
    categories_dict = { cat['name'] : [ (item, 'off') for item in items] for cat in categories }
    
    if ( 'subevent' in request.GET ) and request.event.has_subevents :
        category_maps = SeatCategoryMapping.objects.filter( event_id = request.event.id, subevent_id = subevent_ob.id)
    else :
        category_maps = SeatCategoryMapping.objects.filter( event_id = request.event.id  )

    # setting the 'category item map' in the dict that we will render on if we find it in the intermidaite table
    for cat_map in  category_maps:
        cat_dict = categories_dict[cat_map.layout_category]
        if cat_dict is not None :
            for i,item_tup in enumerate(cat_dict) :
                if cat_map.product.id == item_tup[0].id :
                    categories_dict[cat_map.layout_category][i] = (item_tup[0],'on')
    
    url_reverse = eventreverse(request.event,'plugins:seating_plan:event.seating.displaydata')
    if subevent_ob is not None:
        url_reverse = eventreverse(request.event,'plugins:seating_plan:event.seating.displaydata',kwargs={
            'subevent':subevent_ob.id
        })
    return render(request,'seating_plan/display.html',{'categories':categories_dict,'url_data':url_reverse})


class Mapping :
    def get(self,x):
        return None       



# used to save a specfic seating plan 
class UploadSeating (EventPermissionRequiredMixin,FormView):
    template_name = 'seating_plan/index.html'
    form_class = SeatingForm
    permission = 'can_change_event_settings'
    def get_success_url(self, **kwargs):
        return reverse('plugins:seating_plan:event.seating.display', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['has_subevents'] = self.request.event.has_subevents
        ctx['subevents'] = self.request.event.subevents.all()
        return ctx
        
    def form_valid(self,form) -> str :
    
        file = self.request.FILES['file']
        body_data = json.loads(file.read().decode().replace("'",'"'))
        
        try :
            ser = SeatingPlanSerializer(data ={'name': file.name[:file.name.index('.')]+' new','layout': body_data})
            print(ser.is_valid())
            if ser.is_valid():
                seat_plan = ser.save(organizer=self.request.organizer)
                self.request.event.seating_plan = seat_plan
                self.request.event.save()
                subevent = None
                if 'subevent' in self.request.GET:
                    subevent = SubEvent.objects.get(id=self.request.GET['subevent'])    
                    subevent.seating_plan = seat_plan
                    subevent.save()
                print(generate_seats(self.request.event,subevent,seat_plan,Mapping()))
                messages.success(self.request, _('A seating plan has been added to '+self.request.event.slug+' with success'))
            else :
                messages.error(self.request,_('ERROR'))
        except :
            messages.error(self.request,_('ERROR'))
        if subevent:
            return redirect(self.get_success_url()+'?subevent='+self.request.GET['subevent'])
        return redirect(self.get_success_url())
        
    

def test (request,**kwargs):
    print(Seat.objects.all())
    return HttpResponse(Seat.objects.all())
        