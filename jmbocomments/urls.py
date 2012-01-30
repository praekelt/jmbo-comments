from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('yal.comments.views',
    url(r'^like/(?P<pk>\d+)/$', 'comment_like', name='comment_like'),
    url(r'^flag/(?P<pk>\d+)/$', 'comment_flag', name='comment_flag'),
)