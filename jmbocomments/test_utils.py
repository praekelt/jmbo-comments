from django.utils.crypto import salted_hmac

def generate_security_hash(content_type, object_pk, timestamp):
        info = (content_type, str(object_pk), str(timestamp))
        key_salt = "django.contrib.forms.CommentSecurityForm"
        value = "-".join(info)
        return salted_hmac(key_salt, value).hexdigest()

def params_for_comments(object):
    content_type = '%s.%s' % (object._meta.app_label,
        object._meta.module_name)
    object_pk = object.pk
    timestamp = "1" * 40
    return {
        'content_type': content_type,
        'object_pk': object_pk,
        'timestamp': timestamp,
        'security_hash': generate_security_hash(content_type, object_pk,
            timestamp),
    }

