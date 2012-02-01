from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from jmbocomments.test_utils import params_for_comments
from jmbocomments.models import YALComment, YALCommentFlag
from jmboarticles.models import Article

# when you get the hang of this; write the following tests:


# anonymous user should not be able to post a comment
# anonymous user should not be able to like a comment

# user should only be able to like a comment once.
# user should be able to flag a comment

class CommentTestCase(TestCase):

    fixtures = [
        'article/fixtures/sample-data.json',
        'auth/fixtures/sample-data.json',
    ]

    def setUp(self):
        self.article = Article.published_objects.latest()
        self.article_url = reverse('article_detail', kwargs={
            'pk': self.article.pk,
        })
        self.client = Client(HTTP_REFERER=self.article_url)
        self.client.login(username='admin', password='admin')

    def place_comment(self, obj, **kwargs):
        params = params_for_comments(obj)
        params.update(kwargs)
        response = self.client.post(reverse('comments-post-comment'),
            params)
        self.assertEqual(response.status_code, 302)
        return YALComment.objects.latest('submit_date')

    def flag_comment(self, comment, **headers):
        response = self.client.get(reverse('comment_flag', kwargs={
            'pk': comment.pk,
        }), **headers)
        return comment.flag_set.latest()


    def test_comment_flagging(self):
        """Flagging a comment should result in the flag being set"""
        comment = self.place_comment(self.article, comment='hello world',
            next=self.article_url)
        flag = self.flag_comment(comment)
        self.assertFalse(comment.is_moderated())
        self.assertFalse(comment.is_community_moderated())
        self.assertEqual(flag.flag, YALCommentFlag.SUGGEST_REMOVAL)

    def test_comment_flag_uniques(self):
        """A user is only allowed to flag a comment once"""
        comment = self.place_comment(self.article, comment='hello world',
            next=self.article_url)
        flag = self.flag_comment(comment)
        self.assertEqual(flag.flag_count, 1)
        flag = self.flag_comment(comment)
        self.assertEqual(flag.flag_users.count(), 1)
        self.assertEqual(flag.flag_count, 1)

    def test_comment_community_moderation(self):
        """
        3 unique flags should result in it being moderated
        by the community
        """
        comment = self.place_comment(self.article, comment='hello world',
            next=self.article_url)
        flag = self.flag_comment(comment)
        self.assertEqual(flag.flag_count, 1)
        flag = self.flag_comment(comment, HTTP_VTL_USER_MSISDN=1)
        flag = self.flag_comment(comment, HTTP_VTL_USER_MSISDN=2)
        self.assertEqual(flag.flag_count, 3)
        self.assertEqual(flag.flag, YALCommentFlag.COMMUNITY_REMOVAL)

