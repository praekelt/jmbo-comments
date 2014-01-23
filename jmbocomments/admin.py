from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ungettext
from jmbocomments.models import UserComment, UserCommentFlag


def perform_approve(request, comment):
    #get_or_create fails if more than 1 results returned
    if UserCommentFlag.objects.filter(comment=comment).count() > 1:
        UserCommentFlag.objects.filter(comment=comment).delete()

    fc, created = UserCommentFlag.objects.get_or_create(comment=comment)
    fc.flag = UserCommentFlag.MODERATOR_APPROVAL
    fc.save()

    comment.is_removed = False
    comment.save()


def perform_delete(request, comment):
    #get_or_create fails if more than 1 results returned
    if UserCommentFlag.objects.filter(comment=comment).count() > 1:
        UserCommentFlag.objects.filter(comment=comment).delete()

    fc, created = UserCommentFlag.objects.get_or_create(comment=comment)
    fc.flag = UserCommentFlag.MODERATOR_DELETION
    fc.reason = "This comment was removed by the moderator."
    fc.save()

    comment.is_removed = True
    comment.save()


class UserCommentFlagAdmin(admin.TabularInline):
    model = UserCommentFlag
    extra = 1
    exclude = ['flag_users']
    readonly_fields = ['flag_count']
    fieldsets = (
        ('Moderation',
            {
                'fields': ('flag', 'reason',),
                'classes': ('collapse',),
            }
        ),
    )


class UserCommentFlagModelAdmin(admin.ModelAdmin):
    model = UserCommentFlag
    extra = 1
    exclude = ['flag_users']
    readonly_fields = ['flag_count', 'comment']
    fieldsets = (
        ('Moderation',
            {
                'fields': ('comment', 'flag', 'reason',)
            }
        ),
    )
    list_display = ('comment', 'flag_count', 'flag')


class UserCommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type', 'content_object',)}
        ),
        (_('Content'),
           {'fields': ('user', 'comment')}
        ),
        (_('Metadata'),
           {
            'fields': ('submit_date', 'is_public', 'is_removed', 'like_count'),
            'classes': ('collapse',)
           }
        ),
     )

    list_display = ('content_object', 'content_type', 'user', 'comment',
                    'submit_date', 'is_public', 'is_removed', 'like_count',
                    'latest_flag')
    list_filter = ('submit_date', 'site', 'is_public', 'is_removed',
                    'content_type',)
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username',)
    actions = ["approve_comments", "remove_comments"]
    readonly_fields = ['submit_date', 'content_type', 'content_object', 'user', 'like_count']
    inlines = [UserCommentFlagAdmin]

    def latest_flag(self, instance):
        if instance.flag_set.exists():
            flag = instance.flag_set.latest()
            return flag.flag
        else:
            return ''

    def get_actions(self, request):
        actions = super(UserCommentAdmin, self).get_actions(request)
        # No one is allowed to delete a comment
        actions.pop('delete_selected')
        if not request.user.has_perm('comments.can_moderate'):
            if 'approve_comments' in actions:
                actions.pop('approve_comments')
            if 'remove_comments' in actions:
                actions.pop('remove_comments')
        return actions

    def approve_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_approve,
                        lambda n: ungettext('approved', 'approved', n))
    approve_comments.short_description = _("Approve selected comments")

    def remove_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_delete,
                        lambda n: ungettext('removed', 'removed', n))
    remove_comments.short_description = _("Remove selected comments")

    def _bulk_flag(self, request, queryset, action, done_message):
        """
        Flag, approve, or remove some comments from an admin action. Actually
        calls the `action` argument to perform the heavy lifting.
        """
        n_comments = 0
        for comment in queryset:
            action(request, comment)
            n_comments += 1

        msg = ungettext(u'1 comment was successfully %(action)s.',
                        u'%(count)s comments were successfully %(action)s.',
                        n_comments)
        self.message_user(request, msg % {'count': n_comments, 'action': done_message(n_comments)})

admin.site.register(UserComment, UserCommentAdmin)
admin.site.register(UserCommentFlag, UserCommentFlagModelAdmin)
