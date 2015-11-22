from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', RedirectView.as_view(url='dreamrise')),
    url(r'^dreamrise/', include('dreamrise.urls'), name='dreamrise'),
    # url(r'^search/$', include('haystack.urls')),
    (r'^accounts/', include('allauth.urls')),
)
