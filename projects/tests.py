from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
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
            likes=20,
            is_live=True
        )
        self.post2 = BlogPost.objects.create(
            title="Post 2",
            slug="post-2",
            content="Content 2",
            views=50,
            likes=5,
            is_live=True
        )
        self.post3 = BlogPost.objects.create(
            title="Post 3",
            slug="post-3",
            content="Content 3",
            views=5,
            likes=100,
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

    def test_blog_list_likes_sort(self):
        """Test that the blog list can be sorted by likes (post3, then post1, then post2)"""
        response = self.client.get(reverse('blog_list') + '?sort=likes')
        posts = list(response.context['page_obj'])
        self.assertEqual(posts[0].title, "Post 3") # 100 likes
        self.assertEqual(posts[1].title, "Post 1") # 20 likes
        self.assertEqual(posts[2].title, "Post 2") # 5 likes

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
            response = self.client.get(reverse('project_detail', args=[project.slug]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'project-content')
            self.assertContains(response, 'blog-content')

    def test_project_detail_embeds_gifs(self):
        """Verify GIFs in project descriptions are properly embedded with custom-gif class"""
        response = self.client.get(reverse('project_detail', args=[self.project_default.slug]))
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
        response = self.client.get(reverse('project_detail', args=[self.project_default.slug]))
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
        response = self.client.get(reverse('project_detail', args=[self.project_feature.slug]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="imageModal"', content)
        self.assertIn('id="modalCarousel"', content)
        self.assertIn('data-slide-to="0"', content)
        self.assertIn('data-bs-interval="false"', content)

    def test_gallery_template_lightbox(self):
        """Verify gallery template renders lightbox modal and clickable thumbnails"""
        response = self.client.get(reverse('project_detail', args=[self.project_gallery.slug]))
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


class ProjectSlugTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project1 = Project.objects.create(
            title="Space Shooter 3D",
            category="Games",
            template="default",
            featured=True,
            description="<p>A 3D space combat game</p>"
        )
        self.post1 = BlogPost.objects.create(
            title="Devlog #1",
            slug="devlog-1",
            content="<p>Building the game</p>",
            is_live=True
        )
        self.post1.projects.add(self.project1)

    def test_project_auto_slug_generation(self):
        """Project auto-generates slug on creation from title"""
        self.assertEqual(self.project1.slug, "space-shooter-3d")

    def test_project_custom_slug_preservation(self):
        """Explicitly provided slug is preserved"""
        proj = Project.objects.create(title="My Custom Game", slug="custom-game-slug")
        self.assertEqual(proj.slug, "custom-game-slug")

    def test_project_slug_collision_resolution(self):
        """Duplicate titles get unique numbered suffixes"""
        proj_copy1 = Project.objects.create(title="Space Shooter 3D")
        proj_copy2 = Project.objects.create(title="Space Shooter 3D")
        self.assertEqual(proj_copy1.slug, "space-shooter-3d-1")
        self.assertEqual(proj_copy2.slug, "space-shooter-3d-2")

    def test_project_detail_by_slug_returns_200(self):
        """Accessing project detail via slug returns 200 OK"""
        response = self.client.get(reverse('project_detail', args=[self.project1.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Space Shooter 3D")

    def test_legacy_project_id_url_301_redirects_to_slug(self):
        """Accessing project detail via legacy numeric ID returns 301 Permanent Redirect to canonical slug URL"""
        response = self.client.get(f'/project/{self.project1.pk}/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, reverse('project_detail', args=[self.project1.slug]))

        # Following the redirect reaches the page with 200 OK
        follow_response = self.client.get(f'/project/{self.project1.pk}/', follow=True)
        self.assertEqual(follow_response.status_code, 200)
        self.assertContains(follow_response, "Space Shooter 3D")

    def test_numeric_slug_direct_resolution(self):
        """A project whose title and slug are numeric resolves directly without redirect loop"""
        num_project = Project.objects.create(title="2048", slug="2048")
        response = self.client.get('/project/2048/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2048")

    def test_nonexistent_project_slug_and_id_return_404(self):
        """Nonexistent slug and nonexistent integer ID return 404"""
        res1 = self.client.get('/project/non-existent-slug/')
        self.assertEqual(res1.status_code, 404)
        res2 = self.client.get('/project/99999/')
        self.assertEqual(res2.status_code, 404)

    def test_get_absolute_url(self):
        """Project.get_absolute_url returns canonical slug URL"""
        self.assertEqual(self.project1.get_absolute_url(), f'/project/{self.project1.slug}/')

    def test_templates_render_slug_urls(self):
        """Listing templates and blog detail render links with project slug instead of pk"""
        # Home
        res_home = self.client.get(reverse('home'))
        self.assertContains(res_home, f'/project/{self.project1.slug}/')
        self.assertNotContains(res_home, f'/project/{self.project1.pk}/')

        # Games
        res_games = self.client.get(reverse('games'))
        self.assertContains(res_games, f'/project/{self.project1.slug}/')

        # Blog detail
        res_blog = self.client.get(reverse('blog_detail', args=[self.post1.slug]))
        self.assertContains(res_blog, f'/project/{self.project1.slug}/')

        # Project detail blog link
        res_proj = self.client.get(reverse('project_detail', args=[self.project1.slug]))
        self.assertContains(res_proj, f'/blog/?project={self.project1.slug}')

    def test_blog_list_filter_by_slug_and_legacy_id(self):
        """Blog list filtering works with both slug and legacy ID"""
        res_slug = self.client.get(f'/blog/?project={self.project1.slug}')
        self.assertEqual(res_slug.status_code, 200)
        self.assertContains(res_slug, "Devlog #1")

        res_pk = self.client.get(f'/blog/?project={self.project1.pk}')
        self.assertEqual(res_pk.status_code, 200)
        self.assertContains(res_pk, "Devlog #1")

    def test_admin_prepopulated_fields(self):
        """ProjectAdmin has prepopulated_fields set for slug from title"""
        from django.contrib import admin
        project_admin = admin.site._registry[Project]
        self.assertEqual(project_admin.prepopulated_fields, {'slug': ('title',)})


class EmbedGifsFilterTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_embed_gifs_anchor_tag_with_url_text(self):
        """Anchor tags linking to Giphy GIFs are replaced with clean responsive image links without leaking text"""
        from projects.templatetags.custom_filters import embed_gifs
        input_html = '<p>&nbsp; &nbsp; &nbsp;<a href="https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif">https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif</a><br></p>'
        result = str(embed_gifs(input_html))
        self.assertIn('<img src="https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif" alt="GIF" class="img-fluid mb-3 gifs custom-gif">', result)
        self.assertIn('<a href="https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif" class="gif-link" target="_blank" rel="noopener noreferrer">', result)
        self.assertNotIn('class="gif-link">https://media.giphy.com', result)
        self.assertNotIn('<a href="<a href=', result)
        self.assertNotIn('<img src="<a href=', result)

    def test_embed_gifs_standalone_url(self):
        """Standalone Giphy URLs in text are converted to responsive image links"""
        from projects.templatetags.custom_filters import embed_gifs
        input_html = '<p>Check out gameplay: https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif in action!</p>'
        result = str(embed_gifs(input_html))
        self.assertIn('<img src="https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif" alt="GIF" class="img-fluid mb-3 gifs custom-gif">', result)
        self.assertIn('<a href="https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif" class="gif-link"', result)

    def test_embed_gifs_preserves_existing_img(self):
        """Existing img tags with Giphy sources are not corrupted or double-wrapped"""
        from projects.templatetags.custom_filters import embed_gifs
        input_html = '<p><img src="https://media.giphy.com/media/hHcLqi6GAOeH1Ox2Eo/giphy.gif" alt="Original" class="custom"></p>'
        result = str(embed_gifs(input_html))
        self.assertEqual(result, input_html)


class BlogHomepageAndFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(
            name="Vitor Barbosa",
            title="Software Developer",
            email="vitor@example.com",
            phone="123456789",
            linkedin="https://linkedin.com",
            github="https://github.com",
            itch_io="https://itch.io",
            bio="<p>Full stack and game dev</p>"
        )
        self.proj_featured = Project.objects.create(
            title="Defend the Farm: Strategy Survival Tower Defense",
            slug="defend-the-farm-strategy-survival-tower-defense",
            category="Games",
            featured=True,
            description="<p>Defend the farm game</p>"
        )
        self.proj_other = Project.objects.create(
            title="Super Long Project Name That Definitely Needs Truncating",
            slug="super-long-project-name-that-definitely-needs-truncating",
            category="Full Stack",
            featured=False,
            description="<p>Full stack app</p>"
        )
        self.proj_no_blog = Project.objects.create(
            title="Unblogged Project",
            slug="unblogged-project",
            category="Games",
            featured=False,
            description="<p>No blog exists for this</p>"
        )
        self.post_featured = BlogPost.objects.create(
            title="Major Update for Defend the Farm",
            slug="major-update-for-defend-the-farm",
            content="<p>Exciting new features added.</p>",
            is_live=True,
            featured=True,
        )
        self.post_featured.projects.add(self.proj_featured)

        self.post_other = BlogPost.objects.create(
            title="Devlog for Super Long Project",
            slug="devlog-for-super-long-project",
            content="<p>Building the full stack components.</p>",
            is_live=True,
            featured=False,
        )
        self.post_other.projects.add(self.proj_other)

        self.post_draft = BlogPost.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="<p>Not live yet.</p>",
            is_live=False,
        )

    def test_homepage_blog_cta_renders_posts_and_links(self):
        """Homepage renders 'From the Blog' section with CTA buttons and post excerpts"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "From the Blog")
        self.assertContains(response, "Major Update for Defend the Farm")
        self.assertContains(response, "Explore All Blog Posts")
        self.assertContains(response, "Subscribe to Newsletter")
        self.assertContains(response, reverse('blog_list'))
        self.assertContains(response, reverse('subscribe'))

    def test_homepage_shows_featured_post_when_available(self):
        """Homepage displays featured blog posts in the CTA section"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        blog_posts = list(response.context['blog_posts'])
        self.assertIn(self.post_featured, blog_posts)
        # Draft posts must not appear
        self.assertNotIn(self.post_draft, blog_posts)

    def test_homepage_blog_cta_empty_state(self):
        """Homepage renders blog CTA box even when no live blog posts exist"""
        BlogPost.objects.all().delete()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "From the Blog")
        self.assertContains(response, "Want to Read More?")
        self.assertContains(response, "Explore All Blog Posts")
        self.assertContains(response, "Subscribe to Newsletter")

    def test_blog_list_truncates_project_names_in_filters(self):
        """Project names in filter buttons and badges are truncated to prevent overflow"""
        response = self.client.get(reverse('blog_list'))
        self.assertEqual(response.status_code, 200)
        # Featured project title is truncated with 20 chars (with unicode ellipsis …)
        self.assertContains(response, 'title="Defend the Farm: Strategy Survival Tower Defense"')
        self.assertContains(response, 'Defend the Farm: St\u2026')
        # Full untruncated 49-char string is not rendered in the button inner text
        self.assertNotContains(response, '>Defend the Farm: Strategy Survival Tower Defense<')

    def test_blog_list_featured_projects_vs_dropdown(self):
        """Featured projects appear as top-level buttons while non-featured projects appear in dropdown"""
        response = self.client.get(reverse('blog_list'))
        self.assertEqual(response.status_code, 200)

        # Featured project is in featured_projects
        self.assertIn(self.proj_featured, response.context['featured_projects'])
        # Non-featured project with live blog is in other_projects (dropdown)
        self.assertIn(self.proj_other, response.context['other_projects'])
        # Project without live blog is NOT in filter at all
        self.assertNotIn(self.proj_no_blog, response.context['tagged_projects'])
        self.assertNotIn(self.proj_no_blog, response.context['featured_projects'])
        self.assertNotIn(self.proj_no_blog, response.context['other_projects'])

        # Dropdown exists in HTML
        self.assertContains(response, 'id="moreProjectsDropdown"')
        self.assertContains(response, 'dropdown-menu')
        self.assertContains(response, f'?project={self.proj_other.slug}')

    def test_blog_list_dropdown_active_state_when_selected(self):
        """When a project from the dropdown is active, the dropdown toggle indicates active selection"""
        response = self.client.get(f'/blog/?project={self.proj_other.slug}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_active_in_other'])
        self.assertEqual(response.context['active_project'], self.proj_other)
        # Dropdown toggle button has btn-primary
        self.assertContains(response, 'btn-primary dropdown-toggle')

    def test_admin_featured_actions_and_fields(self):
        """BlogPostAdmin and ProjectAdmin support featured actions and list configuration"""
        from django.contrib import admin
        blog_admin = admin.site._registry[BlogPost]
        proj_admin = admin.site._registry[Project]

        self.assertIn('featured', blog_admin.list_display)
        self.assertIn('featured', blog_admin.list_filter)
        self.assertIn('featured', blog_admin.list_editable)
        self.assertIn('make_featured', blog_admin.actions)
        self.assertIn('remove_featured', blog_admin.actions)

        self.assertIn('featured', proj_admin.list_display)
        self.assertIn('featured', proj_admin.list_filter)
        self.assertIn('featured', proj_admin.list_editable)
        self.assertIn('make_featured', proj_admin.actions)
        self.assertIn('remove_featured', proj_admin.actions)


class BlogLikesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(
            name="Vitor Barbosa",
            title="Full Stack Developer",
            email="vitor@example.com",
            phone="123456789",
            linkedin="https://linkedin.com",
            github="https://github.com",
            itch_io="https://itch.io",
            bio="<p>Full stack and game dev</p>"
        )
        self.post = BlogPost.objects.create(
            title="Awesome Unity Shaders Tutorial",
            slug="awesome-unity-shaders-tutorial",
            content="<p>How to write custom shaders in Unity.</p>",
            is_live=True,
            likes=0,
            views=10,
        )
        self.draft_post = BlogPost.objects.create(
            title="Unpublished Draft Post",
            slug="unpublished-draft-post",
            content="<p>Draft content</p>",
            is_live=False,
            likes=0,
            views=0,
        )

    def test_blog_post_like_standard_post_request(self):
        """Standard form POST to like increments likes, stores in session, and redirects"""
        response = self.client.post(reverse('blog_like', args=[self.post.slug]))
        self.assertRedirects(response, reverse('blog_detail', args=[self.post.slug]))

        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 1)

        # Check session
        session = self.client.session
        self.assertIn(self.post.pk, session.get('liked_posts', []))

    def test_blog_post_like_ajax_request(self):
        """AJAX POST to like returns JSON with liked status and count"""
        response = self.client.post(
            reverse('blog_like', args=[self.post.slug]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)

        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 1)

    def test_blog_post_unlike_toggle_standard(self):
        """Liking an already liked post toggles unlike and decrements likes count"""
        # First like
        self.client.post(reverse('blog_like', args=[self.post.slug]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 1)

        # Second request (unlike)
        response = self.client.post(reverse('blog_like', args=[self.post.slug]))
        self.assertRedirects(response, reverse('blog_detail', args=[self.post.slug]))

        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 0)
        session = self.client.session
        self.assertNotIn(self.post.pk, session.get('liked_posts', []))

    def test_blog_post_unlike_toggle_ajax(self):
        """AJAX requests toggle like and unlike with accurate JSON responses"""
        # First AJAX like
        res1 = self.client.post(
            reverse('blog_like', args=[self.post.slug]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json(), {'liked': True, 'likes_count': 1})

        # Second AJAX unlike
        res2 = self.client.post(
            reverse('blog_like', args=[self.post.slug]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json(), {'liked': False, 'likes_count': 0})

    def test_blog_post_like_draft_returns_404(self):
        """Attempting to like a draft post returns 404"""
        response = self.client.post(reverse('blog_like', args=[self.draft_post.slug]))
        self.assertEqual(response.status_code, 404)

    def test_blog_post_like_nonexistent_returns_404(self):
        """Attempting to like a non-existent post slug returns 404"""
        response = self.client.post(reverse('blog_like', args=['does-not-exist']))
        self.assertEqual(response.status_code, 404)

    def test_blog_post_like_get_request_redirects(self):
        """GET request to blog_like redirects to blog_detail without modifying likes"""
        response = self.client.get(reverse('blog_like', args=[self.post.slug]))
        self.assertRedirects(response, reverse('blog_detail', args=[self.post.slug]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 0)

    def test_blog_detail_renders_like_button_and_unliked_state(self):
        """Blog detail template renders like button in unliked state initially"""
        response = self.client.get(reverse('blog_detail', args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="like-btn"')
        self.assertContains(response, 'Like')
        self.assertFalse(response.context['is_liked'])

    def test_blog_detail_renders_liked_state_from_session(self):
        """Blog detail template reflects liked state when session contains the post ID"""
        session = self.client.session
        session['liked_posts'] = [self.post.pk]
        session.save()

        response = self.client.get(reverse('blog_detail', args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_liked'])
        self.assertContains(response, 'Liked')

    def test_blog_list_and_home_show_likes_count(self):
        """Blog list and Home page display the likes count on blog cards"""
        self.post.likes = 7
        self.post.save()

        # Blog list page
        response_list = self.client.get(reverse('blog_list'))
        self.assertEqual(response_list.status_code, 200)
        self.assertContains(response_list, '7 likes')

        # Home page
        response_home = self.client.get(reverse('home'))
        self.assertEqual(response_home.status_code, 200)
        self.assertContains(response_home, '7 likes')

    def test_admin_blog_post_likes_field(self):
        """BlogPostAdmin includes likes in list_display and readonly_fields"""
        from django.contrib import admin
        blog_admin = admin.site._registry[BlogPost]
        self.assertIn('likes', blog_admin.list_display)
        self.assertIn('likes', blog_admin.readonly_fields)

    def test_multiple_posts_liked_in_same_session(self):
        """Multiple blog posts can be liked and toggled independently in the same session"""
        post2 = BlogPost.objects.create(
            title="Second Blog Post",
            slug="second-blog-post",
            content="<p>More dev content</p>",
            is_live=True,
            likes=0,
        )

        # Like first post
        self.client.post(reverse('blog_like', args=[self.post.slug]))
        # Like second post
        self.client.post(reverse('blog_like', args=[post2.slug]))

        self.post.refresh_from_db()
        post2.refresh_from_db()
        self.assertEqual(self.post.likes, 1)
        self.assertEqual(post2.likes, 1)

        session = self.client.session
        self.assertIn(self.post.pk, session.get('liked_posts', []))
        self.assertIn(post2.pk, session.get('liked_posts', []))

        # Unlike first post only
        self.client.post(reverse('blog_like', args=[self.post.slug]))
        self.post.refresh_from_db()
        post2.refresh_from_db()
        self.assertEqual(self.post.likes, 0)
        self.assertEqual(post2.likes, 1)

        session = self.client.session
        self.assertNotIn(self.post.pk, session.get('liked_posts', []))
        self.assertIn(post2.pk, session.get('liked_posts', []))

    def test_likes_count_never_drops_below_zero(self):
        """Even if unliked when DB count is 0, likes does not become negative"""
        self.post.likes = 0
        self.post.save()

        # Simulate session having post marked as liked while DB likes is 0
        session = self.client.session
        session['liked_posts'] = [self.post.pk]
        session.save()

        self.client.post(reverse('blog_like', args=[self.post.slug]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes, 0)


class AdminMFATest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            password="securepassword123",
        )
        self.totp_device = TOTPDevice.objects.create(
            user=self.user,
            name="default",
            confirmed=True,
        )

    def test_admin_site_is_otp_admin_site(self):
        """Admin site is configured as CustomOTPAdminSite with CustomOTPAdminAuthenticationForm"""
        from django.contrib import admin
        from django_otp.admin import OTPAdminSite
        from projects.admin import CustomOTPAdminSite, CustomOTPAdminAuthenticationForm

        self.assertIsInstance(admin.site, OTPAdminSite)
        self.assertIsInstance(admin.site, CustomOTPAdminSite)
        self.assertEqual(admin.site.login_form, CustomOTPAdminAuthenticationForm)

    def test_admin_unauthenticated_redirects_to_login(self):
        """Unauthenticated requests to /admin/ redirect to the admin login page"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_admin_user_without_mfa_can_login_with_username_and_password(self):
        """A user without MFA configured can log in with standard username & password without an OTP token"""
        no_mfa_user = User.objects.create_superuser(
            username="plain_admin",
            email="plain@example.com",
            password="plainpassword123",
        )
        login_response = self.client.post('/admin/login/', {
            'username': 'plain_admin',
            'password': 'plainpassword123',
            'otp_token': '',
            'next': '/admin/',
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertIn('/admin/', login_response.url)

        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 200)

        # Can also access specific admin pages
        project_admin_response = self.client.get('/admin/projects/project/')
        self.assertEqual(project_admin_response.status_code, 200)

    def test_admin_user_with_unconfirmed_device_can_login_without_token(self):
        """A user with an unconfirmed TOTP device is not locked out and can log in without OTP token"""
        unconfirmed_user = User.objects.create_superuser(
            username="unconfirmed_admin",
            email="unconf@example.com",
            password="unconfirmedpass123",
        )
        TOTPDevice.objects.create(
            user=unconfirmed_user,
            name="unconfirmed_default",
            confirmed=False,
        )
        login_response = self.client.post('/admin/login/', {
            'username': 'unconfirmed_admin',
            'password': 'unconfirmedpass123',
            'otp_token': '',
            'next': '/admin/',
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertIn('/admin/', login_response.url)

        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 200)

    def test_admin_user_with_mfa_cannot_login_without_token(self):
        """A user with confirmed MFA cannot log in without providing an OTP token"""
        login_response = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_token': '',
            'next': '/admin/',
        })
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('Please enter your OTP token.', str(login_response.context['form'].errors))

        # /admin/ remains inaccessible
        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 302)

    def test_admin_unverified_session_redirects_to_login(self):
        """A user logged in without completing OTP verification is blocked from /admin/"""
        self.client.force_login(self.user)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_admin_login_with_valid_totp_token(self):
        """Logging in with correct credentials and valid TOTP code succeeds and grants admin access"""
        from django_otp.oath import totp

        token = str(totp(self.totp_device.bin_key)).zfill(6)
        login_response = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_token': token,
            'next': '/admin/',
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertIn('/admin/', login_response.url)

        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 200)

    def test_admin_login_with_invalid_totp_token(self):
        """Logging in with incorrect TOTP code fails authentication and keeps admin access protected"""
        login_response = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_token': '000000',
            'next': '/admin/',
        })
        # Stays on login page (form error)
        self.assertEqual(login_response.status_code, 200)

        # /admin/ remains inaccessible
        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 302)

    def test_admin_login_with_static_backup_token(self):
        """Logging in with an emergency static backup token succeeds and grants admin access"""
        from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

        static_device = StaticDevice.objects.create(
            user=self.user,
            name="backup",
            confirmed=True,
        )
        backup_token = static_device.token_set.create(token=StaticToken.random_token())

        login_response = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_device': static_device.persistent_id,
            'otp_token': backup_token.token,
            'next': '/admin/',
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertIn('/admin/', login_response.url)

        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 200)

    def test_static_token_is_single_use(self):
        """Emergency static backup tokens are consumed on use and cannot be reused"""
        from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

        static_device = StaticDevice.objects.create(
            user=self.user,
            name="backup",
            confirmed=True,
        )
        backup_token = static_device.token_set.create(token=StaticToken.random_token())
        token_value = backup_token.token

        # First use succeeds
        res1 = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_device': static_device.persistent_id,
            'otp_token': token_value,
            'next': '/admin/',
        })
        self.assertEqual(res1.status_code, 302)

        # Logout
        self.client.logout()

        # Reusing the same token fails
        res2 = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_device': static_device.persistent_id,
            'otp_token': token_value,
            'next': '/admin/',
        })
        self.assertEqual(res2.status_code, 200)

    def test_setup_admin_mfa_management_command(self):
        """setup_admin_mfa command configures TOTP device and backup tokens for a user"""
        from django.core.management import call_command
        import io

        out = io.StringIO()
        call_command('setup_admin_mfa', 'admin_user', backup_tokens=3, stdout=out)
        output = out.getvalue()

        self.assertIn("MFA Setup for user 'admin_user'", output)
        self.assertIn("Secret Key:", output)
        self.assertIn("Setup URI:", output)
        self.assertIn("Emergency Backup Recovery Tokens (3)", output)
        self.assertIn("MFA successfully configured", output)

    def test_setup_admin_mfa_management_command_auto_detects_single_superuser(self):
        """setup_admin_mfa auto-detects the sole superuser when no username is provided"""
        from django.core.management import call_command
        import io

        out = io.StringIO()
        call_command('setup_admin_mfa', backup_tokens=2, stdout=out)
        output = out.getvalue()

        self.assertIn("MFA Setup for user 'admin_user'", output)

    def test_setup_admin_mfa_management_command_reset(self):
        """setup_admin_mfa with --reset replaces existing TOTP device"""
        from django.core.management import call_command
        import io

        old_key = self.totp_device.bin_key

        out = io.StringIO()
        call_command('setup_admin_mfa', 'admin_user', reset=True, stdout=out)
        output = out.getvalue()

        self.assertIn("reset", output)
        new_device = TOTPDevice.objects.get(user=self.user, name="default")
        self.assertNotEqual(new_device.bin_key, old_key)

    def test_setup_admin_mfa_management_command_nonexistent_user(self):
        """setup_admin_mfa raises CommandError for non-existent user"""
        from django.core.management import call_command, CommandError

        with self.assertRaises(CommandError):
            call_command('setup_admin_mfa', 'nonexistent_user_12345')

    def test_unverified_user_cannot_access_project_admin(self):
        """Unverified requests to /admin/projects/project/ redirect to login"""
        self.client.force_login(self.user)
        response = self.client.get('/admin/projects/project/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_verified_user_can_access_project_admin(self):
        """Verified user with OTP completed can access /admin/projects/project/"""
        from django_otp.oath import totp

        token = str(totp(self.totp_device.bin_key)).zfill(6)
        self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_token': token,
            'next': '/admin/projects/project/',
        })
        response = self.client.get('/admin/projects/project/')
        self.assertEqual(response.status_code, 200)

    def test_admin_multi_device_selection(self):
        """When user has multiple devices, CustomOTPAdminAuthenticationForm resolves appropriately"""
        from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

        static_device = StaticDevice.objects.create(
            user=self.user,
            name="backup",
            confirmed=True,
        )
        backup_token = static_device.token_set.create(token=StaticToken.random_token())

        # Test logging in by choosing the static device explicitly
        res = self.client.post('/admin/login/', {
            'username': 'admin_user',
            'password': 'securepassword123',
            'otp_device': static_device.persistent_id,
            'otp_token': backup_token.token,
            'next': '/admin/',
        })
        self.assertEqual(res.status_code, 302)

    def test_user_admin_changelist_shows_mfa_status(self):
        """User admin changelist displays 2FA / MFA status badges and setup links"""
        import django_otp
        plain_user = User.objects.create_user(
            username="plain_staff",
            email="plainstaff@example.com",
            password="pass",
            is_staff=True,
        )
        self.client.force_login(self.user)
        session = self.client.session
        session[django_otp.DEVICE_ID_SESSION_KEY] = self.totp_device.persistent_id
        session.save()

        res = self.client.get('/admin/auth/user/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('✓ Active', content)
        self.assertIn('Not Set', content)
        self.assertIn('[+ Add MFA]', content)

    def test_user_admin_change_form_shows_unconfigured_panel_and_add_mfa_button(self):
        """User admin change form shows unconfigured panel and 'Add / Manage MFA' button for users without 2FA"""
        plain_user = User.objects.create_superuser(
            username="new_admin",
            email="newadmin@example.com",
            password="pass",
        )
        self.client.force_login(plain_user)

        res = self.client.get(f'/admin/auth/user/{plain_user.id}/change/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('2FA / MFA Not Configured', content)
        self.assertIn('Add MFA to Account (Scan QR Code)', content)
        self.assertIn('Add / Manage MFA', content)

    def test_user_admin_change_form_shows_active_panel_when_mfa_configured(self):
        """User admin change form shows active 2FA status and management buttons when MFA is configured"""
        import django_otp
        self.client.force_login(self.user)
        session = self.client.session
        session[django_otp.DEVICE_ID_SESSION_KEY] = self.totp_device.persistent_id
        session.save()

        res = self.client.get(f'/admin/auth/user/{self.user.id}/change/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Two-Factor Authentication Active', content)
        self.assertIn('Re-configure / Show QR', content)
        self.assertIn('Backup Recovery Codes', content)
        self.assertIn('Disable 2FA', content)

    def test_user_admin_mfa_setup_get_renders_qr_code_and_secret_key(self):
        """Visiting MFA setup page renders high-resolution scannable QR code and Base32 secret key"""
        plain_user = User.objects.create_superuser(
            username="qr_test_user",
            email="qr@example.com",
            password="pass",
        )
        self.client.force_login(plain_user)

        res = self.client.get(f'/admin/auth/user/{plain_user.id}/mfa/setup/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('data:image/png;base64,', content)
        self.assertIn('Scan QR Code with Authenticator App', content)
        self.assertIn('secretKeyText', content)
        self.assertIn('Verify & Activate 2FA', content)

    def test_user_admin_mfa_setup_post_invalid_token_shows_error(self):
        """Submitting an invalid 6-digit token on MFA setup displays a helpful error message"""
        plain_user = User.objects.create_superuser(
            username="invalid_otp_user",
            email="invalid@example.com",
            password="pass",
        )
        self.client.force_login(plain_user)

        # GET creates unconfirmed device
        self.client.get(f'/admin/auth/user/{plain_user.id}/mfa/setup/')
        dev = TOTPDevice.objects.get(user=plain_user, confirmed=False)

        res = self.client.post(f'/admin/auth/user/{plain_user.id}/mfa/setup/', {
            'otp_token': '000000',
            'device_id': dev.pk,
        })
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Invalid code', content)
        self.assertFalse(TOTPDevice.objects.get(user=plain_user).confirmed)

    def test_user_admin_mfa_setup_post_valid_token_confirms_device_and_generates_backup_tokens(self):
        """Submitting valid 6-digit TOTP code confirms device and provides 8 single-use emergency backup tokens"""
        from django_otp.oath import totp
        from django_otp.plugins.otp_static.models import StaticDevice

        plain_user = User.objects.create_superuser(
            username="confirm_otp_user",
            email="confirm@example.com",
            password="pass",
        )
        self.client.force_login(plain_user)

        self.client.get(f'/admin/auth/user/{plain_user.id}/mfa/setup/')
        dev = TOTPDevice.objects.get(user=plain_user, confirmed=False)
        valid_token = str(totp(dev.bin_key)).zfill(6)

        res = self.client.post(f'/admin/auth/user/{plain_user.id}/mfa/setup/', {
            'otp_token': valid_token,
            'device_id': dev.pk,
        })
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Two-Factor Authentication is now active', content)
        self.assertIn('Emergency Backup Recovery Tokens', content)

        # Device is confirmed in database
        dev.refresh_from_db()
        self.assertTrue(dev.confirmed)

        # Static recovery tokens are created
        static_dev = StaticDevice.objects.get(user=plain_user, confirmed=True)
        self.assertEqual(static_dev.token_set.count(), 8)

    def test_user_admin_mfa_backup_tokens_view_and_generate_fresh_tokens(self):
        """Backup tokens view displays active recovery tokens and allows regenerating 8 new tokens"""
        import django_otp
        from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

        self.client.force_login(self.user)
        session = self.client.session
        session[django_otp.DEVICE_ID_SESSION_KEY] = self.totp_device.persistent_id
        session.save()

        static_dev = StaticDevice.objects.create(user=self.user, name="backup", confirmed=True)
        t1 = static_dev.token_set.create(token=StaticToken.random_token())

        # GET tokens view
        res = self.client.get(f'/admin/auth/user/{self.user.id}/mfa/backup-tokens/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(t1.token, res.content.decode('utf-8'))

        # POST regenerate
        res_post = self.client.post(f'/admin/auth/user/{self.user.id}/mfa/backup-tokens/', {
            'action': 'generate',
        })
        self.assertEqual(res_post.status_code, 200)
        self.assertEqual(static_dev.token_set.count(), 8)
        self.assertFalse(static_dev.token_set.filter(token=t1.token).exists())

    def test_user_admin_mfa_disable_flow(self):
        """MFA disable view asks confirmation and completely removes 2FA devices and backup tokens"""
        import django_otp
        from django_otp.plugins.otp_static.models import StaticDevice

        self.client.force_login(self.user)
        session = self.client.session
        session[django_otp.DEVICE_ID_SESSION_KEY] = self.totp_device.persistent_id
        session.save()

        StaticDevice.objects.create(user=self.user, name="backup", confirmed=True)

        # GET confirmation page
        res_get = self.client.get(f'/admin/auth/user/{self.user.id}/mfa/disable/')
        self.assertEqual(res_get.status_code, 200)
        self.assertIn('Are you sure you want to disable Two-Factor Authentication', res_get.content.decode('utf-8'))

        # POST to disable
        res_post = self.client.post(f'/admin/auth/user/{self.user.id}/mfa/disable/')
        self.assertEqual(res_post.status_code, 302)
        self.assertIn(f'/admin/auth/user/{self.user.id}/change/', res_post.url)

        self.assertEqual(TOTPDevice.objects.filter(user=self.user).count(), 0)
        self.assertEqual(StaticDevice.objects.filter(user=self.user).count(), 0)

    def test_user_admin_mfa_setup_permission_denied_for_non_privileged_user(self):
        """Staff user without change_user permission cannot manage MFA for other users"""
        regular_staff = User.objects.create_user(
            username="regular_staff",
            email="regular@example.com",
            password="pass",
            is_staff=True,
        )
        other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="pass",
            is_staff=True,
        )
        self.client.force_login(regular_staff)

        res = self.client.get(f'/admin/auth/user/{other_user.id}/mfa/setup/')
        self.assertEqual(res.status_code, 403)
