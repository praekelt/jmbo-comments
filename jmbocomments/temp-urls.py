from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.conf import settings
from django.http import HttpResponse

admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^article/', include('jmboarticles.urls')),
    
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^yal/comments/', include('jmbocomments.urls')),
   )
