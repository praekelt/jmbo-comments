from django.db import models
from django.contrib.comments.models import BaseCommentAbstractModel
from django.contrib.comments.managers import CommentManager
from django.contrib.comments.moderation import CommentModerator
from django.contrib.comments.signals import comment_was_flagged
from django.contrib.auth.models import User


class UserComment(BaseCommentAbstractModel):
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    user = models.ForeignKey(User, related_name='comments') # user is always required
    comment = models.TextField(max_length=3000)

    submit_date = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField()
    is_removed = models.BooleanField(default=False)

    like_count = models.PositiveIntegerField(default=0)
    like_users = models.ManyToManyField(User, related_name='liked_comments')

    objects = CommentManager()

    def is_community_moderated(self):
        return self.community_moderation_flags().exists()

    def community_moderation_flags(self):
        return self.flag_set.filter(
            flag=UserCommentFlag.COMMUNITY_REMOVAL)

    def moderation_flags(self):
        return self.flag_set.filter(
            flag=UserCommentFlag.MODERATOR_DELETION)

    def is_moderated(self):
        return self.moderation_flags().exists()

    class Meta:
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __unicode__(self):
        return '%s: %s...' % (self.user, self.comment[:50])

class UserCommentFlag(models.Model):
    # Constants for flag types
    SUGGEST_REMOVAL = "removal suggestion"
    COMMUNITY_REMOVAL = "removed by community moderation"
    MODERATOR_DELETION = "moderator deletion"
    MODERATOR_APPROVAL = "moderator approval"

    comment = models.ForeignKey(UserComment, related_name='flag_set')
    flag = models.CharField('flag', choices=((opt,opt) for opt in [
            SUGGEST_REMOVAL,
            COMMUNITY_REMOVAL,
            MODERATOR_DELETION,
            MODERATOR_APPROVAL
        ]), max_length=255, db_index=True, blank=True)
    flag_count = models.PositiveIntegerField(default=0)
    flag_users = models.ManyToManyField(User, related_name='flagged_comments')
    last_flag_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = 'comment moderation flag'
        get_latest_by = 'last_flag_date'

    def __unicode__(self):
        return 'Flagged comment'


class UserCommentModerator(CommentModerator):

    def check_for_duplicate_comment_submission(self, comment, content_type,
                                        object_pk, user):
        """
        Before saving to the db check if we've already written a comment
        for this user with content_type & object_pk with the exact same
        comment text. If so, have the signal return False so it isn't written
        to the database to prevent duplication submissions.
        """
        if user.is_anonymous():
            return False
        else:
            comments = UserComment.objects.filter(user=user,
                content_type=content_type, object_pk=object_pk)
            if comments.exists():
                return comments.latest('submit_date').comment != comment.comment
            else:
                return True

