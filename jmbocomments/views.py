from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse


from models import YALComment, YALCommentFlag

def comment_like(request, pk):

    if request.user.is_authenticated():
        comment = get_object_or_404(YALComment, pk=pk)

        # has the user liked this comment before?
        if not request.user.liked_comments.filter(pk=comment.pk).exists():
            comment.like_count += 1
            comment.like_users.add(request.user)
            comment.save()

    # if HTTP_REFERER is giving problems you can use the cotent_type and object_pk
    # of comment to redirect; see: django.contrib.contenttypes.views.shortcut
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))


def comment_flag(request, pk):
    # this might be considered a downvote, perhaps not a bad idea to have upvote/ downvote
    # and auto-moderate comments.
    comment = get_object_or_404(YALComment, pk=pk)
    if request.user.is_authenticated():
        if not request.user.flagged_comments.filter(comment=comment).exists():
            fc, created = YALCommentFlag.objects.get_or_create(comment=comment)
            fc.flag_count += 1
            if fc.flag_count > 2:
                fc.flag = YALCommentFlag.COMMUNITY_REMOVAL
                fc.reason = "This comment was removed by the YoungAfricaLive community."
            else:
                fc.flag = YALCommentFlag.SUGGEST_REMOVAL
                fc.reason = "Reported for moderation by the YoungAfricaLive community."

            fc.save()
            fc.flag_users.add(request.user)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))
