# Register your receivers here

from django.urls import reverse
from django.dispatch import receiver

from django.utils.translation import gettext_lazy as _
import os

from pretix.base.models import (
    SeatCategoryMapping,
)
from pretix.presale.signals import render_seating_plan
from .get_grouped_items import get_grouped_items
from .get_grouped_items import item_group_by_category
from django.template import Context, Template
from pretix.multidomain.urlreverse import eventreverse
from pretix.control.signals import nav_event




@receiver(nav_event, dispatch_uid="seating_plan_nav")
def control_nav_import(sender, request=None, **kwargs):
    if not request.user.has_event_permission(request.organizer, request.event, 'can_change_event_settings', request=request):
        return []

    if request.event.has_subevents:    
            return [{
            'label': _('Seating'),
            'url': reverse('plugins:seating_plan:event.seating.upload', kwargs={
                'event': request.event.slug,
                'organizer': request.event.organizer.slug,
            }),
            'active': False,
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="14" viewBox="0 0 4.7624999 3.7041668" class="svg-icon"><path d="m 1.9592032,1.8522629e-4 c -0.21468,0 -0.38861,0.17394000371 -0.38861,0.38861000371 0,0.21466 0.17393,0.38861 0.38861,0.38861 0.21468,0 0.3886001,-0.17395 0.3886001,-0.38861 0,-0.21467 -0.1739201,-0.38861000371 -0.3886001,-0.38861000371 z m 0.1049,0.84543000371 c -0.20823,-0.0326 -0.44367,0.12499 -0.39998,0.40462997 l 0.20361,1.01854 c 0.0306,0.15316 0.15301,0.28732 0.3483,0.28732 h 0.8376701 v 0.92708 c 0,0.29313 0.41187,0.29447 0.41187,0.005 v -1.19115 c 0,-0.14168 -0.0995,-0.29507 -0.29094,-0.29507 l -0.65578,-10e-4 -0.1757,-0.87644 C 2.3042533,0.95300523 2.1890432,0.86500523 2.0641032,0.84547523 Z m -0.58549,0.44906997 c -0.0946,-0.0134 -0.20202,0.0625 -0.17829,0.19172 l 0.18759,0.91054 c 0.0763,0.33956 0.36802,0.55914 0.66042,0.55914 h 0.6015201 c 0.21356,0 0.21448,-0.32143 -0.003,-0.32143 H 2.1954632 c -0.19911,0 -0.36364,-0.11898 -0.41341,-0.34107 l -0.17777,-0.87126 c -0.0165,-0.0794 -0.0688,-0.11963 -0.12557,-0.12764 z"></path></svg>',
            'children': [
                {
                    'label': _('Display Seating Plans'),
                    'url': reverse('plugins:seating_plan:event.seating.subevents', kwargs={
                        'event': request.event.slug,
                        'organizer': request.event.organizer.slug
                    })
                },
                {
                    'label': _('Upload Seating Plans'),
                    'url': reverse('plugins:seating_plan:event.seating.upload', kwargs={
                        'event': request.event.slug,
                        'organizer': request.event.organizer.slug
                    })                
                }
            ]
        }
        ]
    else:
            return [
                {
            'label': _('Seating'),
            'url': reverse('plugins:seating_plan:event.seating.upload', kwargs={
                'event': request.event.slug,
                'organizer': request.event.organizer.slug,
            }),
            'active': False,
            'icon': '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="14" viewBox="0 0 4.7624999 3.7041668" class="svg-icon"><path d="m 1.9592032,1.8522629e-4 c -0.21468,0 -0.38861,0.17394000371 -0.38861,0.38861000371 0,0.21466 0.17393,0.38861 0.38861,0.38861 0.21468,0 0.3886001,-0.17395 0.3886001,-0.38861 0,-0.21467 -0.1739201,-0.38861000371 -0.3886001,-0.38861000371 z m 0.1049,0.84543000371 c -0.20823,-0.0326 -0.44367,0.12499 -0.39998,0.40462997 l 0.20361,1.01854 c 0.0306,0.15316 0.15301,0.28732 0.3483,0.28732 h 0.8376701 v 0.92708 c 0,0.29313 0.41187,0.29447 0.41187,0.005 v -1.19115 c 0,-0.14168 -0.0995,-0.29507 -0.29094,-0.29507 l -0.65578,-10e-4 -0.1757,-0.87644 C 2.3042533,0.95300523 2.1890432,0.86500523 2.0641032,0.84547523 Z m -0.58549,0.44906997 c -0.0946,-0.0134 -0.20202,0.0625 -0.17829,0.19172 l 0.18759,0.91054 c 0.0763,0.33956 0.36802,0.55914 0.66042,0.55914 h 0.6015201 c 0.21356,0 0.21448,-0.32143 -0.003,-0.32143 H 2.1954632 c -0.19911,0 -0.36364,-0.11898 -0.41341,-0.34107 l -0.17777,-0.87126 c -0.0165,-0.0794 -0.0688,-0.11963 -0.12557,-0.12764 z"></path></svg>',
            'children': [
                {
                    'label': _('Display Seating Plan'),
                    'url': reverse('plugins:seating_plan:event.seating.display', kwargs={
                        'event': request.event.slug,
                        'organizer': request.event.organizer.slug
                    })
                },
                {
                    'label': _('Upload Seating Plan'),
                    'url': reverse('plugins:seating_plan:event.seating.upload', kwargs={
                        'event': request.event.slug,
                        'organizer': request.event.organizer.slug
                    })                
                }
            ]
                }
            ]










@receiver(render_seating_plan,dispatch_uid="render_seating_plan_1")
def render_seating_plan(sender,request, **kwargs):

    items_final = []
    seat_guid = ''
    subevent= None
    if 'subevent' in kwargs:
        subevent = kwargs['subevent']
    if 'category_seat' in request.GET :
        category_seat = request.GET['category_seat']
        seat_guid = request.GET.get('seat_guid',False)
        if 'subevent' in kwargs:
            cats = SeatCategoryMapping.objects.filter(
        layout_category= category_seat,
        subevent_id = subevent.id)
        else :
            cats = SeatCategoryMapping.objects.filter(
        layout_category= category_seat,
        event_id = request.event.id)
        print('cats ==>',cats)
        itemsf =  [ct.product for ct in cats ]
        
        items, display_add_to_cart = get_grouped_items(
                request.event,    
                subevent,
                filter_items=request.GET.getlist('item'),
                filter_categories=request.GET.getlist('category'),
                require_seat=None,
                channel=request.sales_channel.identifier,
                memberships=(
                    request.customer.usable_memberships(
                        for_event=subevent or request.event,
                        testmode=request.event.testmode
                    ) if getattr(request, 'customer', None) else None
                ),
            )

        for i in items:
            if i in itemsf:
                items_final.append(i)
        

    
    script_dir = os.path.dirname(__file__)
    rel_dir = 'templates/seating_plan/seatingplan.html'
    abs_file_path = os.path.join(script_dir, rel_dir)

    f = open(abs_file_path)
    content = f.read()
    template = Template(content)

    url_reverse = eventreverse(request.event,'plugins:seating_plan:event.seating.displaydata')
    url_reverse_assign = eventreverse(request.event,'plugins:seating_plan:event.seating.productassign')
    if subevent is not None:
        url_reverse = eventreverse(request.event,'plugins:seating_plan:event.seating.displaydata',kwargs={
            'subevent':subevent.id
        })
        url_reverse_assign = eventreverse(request.event,'plugins:seating_plan:event.seating.productassign',kwargs={
            'subevent':subevent.id
        })
    if 'category_seat' in request.GET :
        product = True
    else :
        product = False
    
    context = Context({'active_prod':product,'items_by_category_seats':item_group_by_category(items_final) , 'seat_guid': seat_guid,'url_data': url_reverse,'url_data_assign':url_reverse_assign})
    return template.render(context)


    