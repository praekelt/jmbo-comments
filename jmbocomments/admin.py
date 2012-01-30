from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ungettext
from yal.comments.models import YALComment, YALCommentFlag

def perform_flag(*args, **kwargs):
    raise NotImplemented, 'work in progress'

def perform_approve(*args, **kwargs):
    raise NotImplemented, 'work in progress'

def perform_delete(*args, **kwargs):
    raise NotImplemented, 'work in progress'

class YALCommentFlagAdmin(admin.TabularInline):
    model = YALCommentFlag
    extra = 1
    exclude = ['flag_users']
    readonly_fields = ['flag_count']

class YALCommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type', 'content_object',)}
        ),
        (_('Content'),
           {'fields': ('user', 'comment')}
        ),
        (_('Metadata'),
           {'fields': ('submit_date', 'is_public', 'is_removed', 'like_count')}
        ),
     )

    list_display = ('content_object', 'content_type', 'user', 'comment',
                    'submit_date', 'is_public', 'is_removed', 'like_count',
                    'latest_flag')
    list_filter = ('submit_date', 'site', 'is_public', 'is_removed')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username',)
    actions = ["flag_comments", "approve_comments", "remove_comments"]
    readonly_fields = ['submit_date', 'content_type', 'content_object', 'user', 'like_count']
    inlines = [YALCommentFlagAdmin]

    def latest_flag(self, instance):
        if instance.flag_set.exists():
            flag = instance.flag_set.latest()
            return flag.flag
        else:
            return ''

    def get_actions(self, request):
        actions = super(YALCommentAdmin, self).get_actions(request)
        # Only superusers should be able to delete the comments from the DB.
        if not request.user.is_superuser and 'delete_selected' in actions:
            actions.pop('delete_selected')
        if not request.user.has_perm('comments.can_moderate'):
            if 'approve_comments' in actions:
                actions.pop('approve_comments')
            if 'remove_comments' in actions:
                actions.pop('remove_comments')
        return actions

    def flag_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_flag,
                        lambda n: ungettext('flagged', 'flagged', n))
    flag_comments.short_description = _("Flag selected comments")

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

admin.site.register(YALComment, YALCommentAdmin)
admin.site.register(YALCommentFlag)