from django.test import TestCase, Client
from django.urls import reverse
from .models import BlogPost, Project

class BlogSortTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create some projects
        self.project1 = Project.objects.create(title="Project 1")
        self.project2 = Project.objects.create(title="Project 2")
        
        # Create blog posts with different views and creation dates
        self.post1 = BlogPost.objects.create(
            title="Post 1",
            slug="post-1",
            content="Content 1",
            views=10,
            is_live=True
        )
        self.post2 = BlogPost.objects.create(
            title="Post 2",
            slug="post-2",
            content="Content 2",
            views=50,
            is_live=True
        )
        self.post3 = BlogPost.objects.create(
            title="Post 3",
            slug="post-3",
            content="Content 3",
            views=5,
            is_live=True
        )
        # Manually adjust created_on is hard because of auto_now_add, 
        # but the order_by will work for views at least.
        # Default order is -created_on, so post3 should be first by date if created last.
        
    def test_blog_list_default_sort(self):
        """Test that the blog list defaults to sorting by latest (post3, then post2, then post1)"""
        response = self.client.get(reverse('blog_list'))
        posts = list(response.context['page_obj'])
        self.assertEqual(posts[0].title, "Post 3")
        self.assertEqual(posts[1].title, "Post 2")
        self.assertEqual(posts[2].title, "Post 1")

    def test_blog_list_views_sort(self):
        """Test that the blog list can be sorted by views (post2, then post1, then post3)"""
        response = self.client.get(reverse('blog_list') + '?sort=views')
        posts = list(response.context['page_obj'])
        self.assertEqual(posts[0].title, "Post 2") # 50 views
        self.assertEqual(posts[1].title, "Post 1") # 10 views
        self.assertEqual(posts[2].title, "Post 3") # 5 views

    def test_blog_list_explicit_date_sort(self):
        """Test that the blog list can be explicitly sorted by date"""
        response = self.client.get(reverse('blog_list') + '?sort=date')
        posts = list(response.context['page_obj'])
        self.assertEqual(posts[0].title, "Post 3")
        self.assertEqual(posts[1].title, "Post 2")
        self.assertEqual(posts[2].title, "Post 1")
