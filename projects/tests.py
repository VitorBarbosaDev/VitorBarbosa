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
