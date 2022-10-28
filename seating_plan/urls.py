
from django.conf.urls import re_path

from pretix.api.urls import event_router
from .views import retrieve,seat_product_assign
from .seatingView import UploadSeating,DisplaySeating,DisplaySeriesTable,test
event_patterns  = [
    re_path(r'seating_displaydata/$', retrieve, name='event.seating.displaydata'),
    re_path(r'^(?P<subevent>[0-9]+)/seating_displaydata/$', retrieve, name='event.seating.displaydata') ,
    re_path(r'^seating_productassign/$', seat_product_assign, name='event.seating.productassign'),
    re_path(r'^(?P<subevent>[0-9]+)/seating_productassign/$', seat_product_assign, name='event.seating.productassign')

]

urlpatterns = [
        re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/seating/$', UploadSeating.as_view(), name='event.seating.upload'),
        re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/seating/display$', DisplaySeating, name='event.seating.display'),
        re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/seating/subevents$',DisplaySeriesTable, name='event.seating.subevents'),
        re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/seating/test$', test, name='event.seating.test'),
]