from django.test import TestCase, Client
from django.urls import reverse
from .models import BlogPost, Project, Profile

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


class ProjectImageScalingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(
            name="Vitor Barbosa",
            title="Full Stack Developer",
            bio="<p>Bio with https://media.giphy.com/media/example/giphy.gif</p>"
        )
        self.project_default = Project.objects.create(
            title="Default Project",
            category="Full Stack",
            template="default",
            featured=True,
            description='<p>Sample project with pasted image <img src="https://example.com/screenshot.png" alt="screenshot"> and https://media.giphy.com/media/demo/giphy.gif</p>'
        )
        self.project_gallery = Project.objects.create(
            title="Gallery Project",
            category="Games",
            template="gallery",
            description='<p>Gallery description <img src="https://example.com/game.png"></p>'
        )
        self.project_feature = Project.objects.create(
            title="Feature Project",
            category="Full Stack",
            template="feature",
            description='<p>Feature description</p>'
        )

    def test_project_detail_templates_render_content_scaling_classes(self):
        """Verify project detail views render project-content and blog-content classes for image scaling"""
        for project in [self.project_default, self.project_gallery, self.project_feature]:
            response = self.client.get(reverse('project_detail', args=[project.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'project-content')
            self.assertContains(response, 'blog-content')
            self.assertContains(response, 'project-hero-img')

    def test_project_detail_embeds_gifs(self):
        """Verify GIFs in project descriptions are properly embedded with custom-gif class"""
        response = self.client.get(reverse('project_detail', args=[self.project_default.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'custom-gif')

    def test_project_list_card_images_have_uniform_scaling_classes(self):
        """Verify card images across project listings use project-card-img and blog-card-img"""
        for url_name in ['home', 'full_stack', 'games']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'project-card-img')
            self.assertContains(response, 'blog-card-img')

    def test_home_page_bio_has_content_scaling_and_gif_support(self):
        """Verify home page profile bio has blog-content styling and embeds GIFs"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'blog-content')
        self.assertContains(response, 'custom-gif')
