from django.contrib.auth.middleware import RemoteUserMiddleware
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

class VodacomTanzaniaRemoteUserMiddleware(RemoteUserMiddleware):
    header = 'HTTP_VTL_USER_MSISDN'
    create_unknown_user = True
