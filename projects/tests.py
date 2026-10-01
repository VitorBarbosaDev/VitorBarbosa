from django.test import TestCase, Client
from django.urls import reverse
from .models import BlogPost, Project, Profile, ProjectImage, BlogImage

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

    def test_project_detail_embeds_gifs(self):
        """Verify GIFs in project descriptions are properly embedded with custom-gif class"""
        response = self.client.get(reverse('project_detail', args=[self.project_default.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'custom-gif')

    def test_project_list_card_images_have_uniform_scaling_classes(self):
        """Verify card images across project listings use card-img-top"""
        for url_name in ['full_stack', 'games']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'card-img-top')


class AdminSummernoteConfigTest(TestCase):
    def test_summernote_settings_configuration(self):
        """Verify SUMMERNOTE_CONFIG includes custom theme toggle, custom colors, and fonts"""
        from django.conf import settings
        config = getattr(settings, 'SUMMERNOTE_CONFIG', {})
        self.assertTrue(config.get('iframe'))
        
        summernote = config.get('summernote', {})
        toolbar_buttons = [item for group in summernote.get('toolbar', []) for item in group[1]]
        self.assertIn('themeToggle', toolbar_buttons)
        self.assertIn('Roboto', summernote.get('fontNames', []))
        self.assertIn('Lato', summernote.get('fontNames', []))
        
        # Verify color palette has site dark bg (#121212) and accent green (#4caf50)
        flat_colors = [color for row in summernote.get('colors', []) for color in row]
        self.assertIn('#121212', flat_colors)
        self.assertIn('#4caf50', flat_colors)
        self.assertIn('#e0e0e0', flat_colors)
        
        # Verify custom CSS & JS are registered
        self.assertTrue(any('admin_summernote.css' in css for css in config.get('css', ())))
        self.assertTrue(any('admin_summernote.js' in js for js in config.get('js', ())))

    def test_admin_classes_media_registration(self):
        """Verify ProjectAdmin, BlogPostAdmin, and ProfileAdmin include admin_custom.css and admin_custom.js"""
        from django.contrib import admin
        from .models import Project, BlogPost, Profile
        
        for model in [Project, BlogPost, Profile]:
            model_admin = admin.site._registry[model]
            media = model_admin.media
            self.assertTrue(any('admin_custom.css' in str(css) for css in media._css.values()))
            self.assertTrue(any('admin_custom.js' in str(js) for js in media._js))

    def test_summernote_editor_iframe_response(self):
        """Verify Summernote editor iframe view returns 200 and loads custom CSS and JS"""
        response = self.client.get(reverse('django_summernote-editor', kwargs={'id': 'id_content'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin_summernote.css')
        self.assertContains(response, 'admin_summernote.js')
        self.assertContains(response, 'fonts.googleapis.com')

    def test_static_admin_files_exist_and_contain_theme_rules(self):
        """Verify static CSS and JS files exist and define dark/light theme toggle rules"""
        import os
        from django.conf import settings
        
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'projects')
        
        summernote_css_path = os.path.join(static_dir, 'css', 'admin_summernote.css')
        summernote_js_path = os.path.join(static_dir, 'js', 'admin_summernote.js')
        admin_custom_css_path = os.path.join(static_dir, 'css', 'admin_custom.css')
        admin_custom_js_path = os.path.join(static_dir, 'js', 'admin_custom.js')
        
        for path in [summernote_css_path, summernote_js_path, admin_custom_css_path, admin_custom_js_path]:
            self.assertTrue(os.path.exists(path), f"File {path} does not exist")
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertGreater(len(content), 0, f"File {path} is empty")
        
        # Verify specific rules in admin_summernote.css
        with open(summernote_css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
            self.assertIn('editor-dark-mode', css_content)
            self.assertIn('editor-light-mode', css_content)
            self.assertIn('#121212', css_content)
            self.assertIn('#4caf50', css_content)
            self.assertIn('btn-theme-toggle', css_content)

        # Verify specific rules in admin_summernote.js
        with open(summernote_js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
            self.assertIn('themeToggle', js_content)
            self.assertIn('admin_summernote_theme', js_content)
            self.assertIn('editor-dark-mode', js_content)

        # Verify specific rules in admin_custom.js
        with open(admin_custom_js_path, 'r', encoding='utf-8') as f:
            admin_js_content = f.read()
            self.assertIn('summernote-theme-bar', admin_js_content)
            self.assertIn('btn-theme-dark', admin_js_content)
            self.assertIn('btn-theme-light', admin_js_content)


class LightboxModalTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.img1 = ProjectImage.objects.create(caption="Screenshot 1")
        self.img2 = ProjectImage.objects.create(caption="Screenshot 2")

        self.project_default = Project.objects.create(
            title="Default With Images",
            category="Full Stack",
            template="default",
            description="<p>Project description</p>"
        )
        self.project_default.additional_images.add(self.img1, self.img2)

        self.project_feature = Project.objects.create(
            title="Feature With Images",
            category="Full Stack",
            template="feature",
            description="<p>Feature description</p>"
        )
        self.project_feature.additional_images.add(self.img1, self.img2)

        self.project_gallery = Project.objects.create(
            title="Gallery With Images",
            category="Games",
            template="gallery",
            description="<p>Gallery description</p>"
        )
        self.project_gallery.additional_images.add(self.img1, self.img2)

        self.blog_post = BlogPost.objects.create(
            title="Test Post With Screenshots",
            slug="test-post-screenshots",
            content="<p>Blog post content</p>",
            is_live=True
        )
        self.blog_img = BlogImage.objects.create(
            blog_post=self.blog_post,
            caption="Blog Screenshot 1"
        )

    def test_default_template_lightbox_no_auto_cycling_or_conflicts(self):
        """Verify default template modal has data-bs-interval=false and no data-bs-ride on modal carousel"""
        response = self.client.get(reverse('project_detail', args=[self.project_default.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="imageModal"', content)
        self.assertIn('id="modalCarousel"', content)
        self.assertIn('data-bs-interval="false"', content)
        # Ensure modal carousel does not have data-bs-ride="carousel"
        self.assertNotIn('<div id="modalCarousel" class="carousel slide" data-bs-ride="carousel">', content)
        # Ensure carousel images do not have duplicate data-bs-toggle="modal"
        self.assertNotIn('carousel-image" alt="Screenshot 1" data-bs-toggle="modal"', content)
        self.assertIn('modal-carousel-img', content)

    def test_feature_template_lightbox(self):
        """Verify feature template modal renders cleanly with data-slide-to on thumbnails"""
        response = self.client.get(reverse('project_detail', args=[self.project_feature.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="imageModal"', content)
        self.assertIn('id="modalCarousel"', content)
        self.assertIn('data-slide-to="0"', content)
        self.assertIn('data-bs-interval="false"', content)

    def test_gallery_template_lightbox(self):
        """Verify gallery template renders lightbox modal and clickable thumbnails"""
        response = self.client.get(reverse('project_detail', args=[self.project_gallery.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="imageModal"', content)
        self.assertIn('id="modalCarousel"', content)
        self.assertIn('project-screenshot', content)
        self.assertIn('data-slide-to="0"', content)

    def test_blog_detail_lightbox_modal(self):
        """Verify blog detail renders blogImageModal and blog-screenshot images"""
        response = self.client.get(reverse('blog_detail', args=[self.blog_post.slug]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="blogImageModal"', content)
        self.assertIn('blog-screenshot', content)
        self.assertIn('modal-carousel-img', content)

    def test_style_css_contains_lightbox_dark_theme(self):
        """Verify style.css contains dark theme modal rules and responsive containment"""
        import os
        from django.conf import settings
        css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'style.css')
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
            self.assertIn('.modal-content', css)
            self.assertIn('#1e1e1e', css)
            self.assertIn('.modal-carousel-img', css)
            self.assertIn('object-fit: contain', css)
