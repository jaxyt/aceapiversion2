"""aceapiversion2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.contrib import admin
from django.urls import path, include
from compiler import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('agents/', include('agents.urls', namespace='agents')),
    path('compilev3/',views.test_send, name="test"),
    path('compile/', views.compile, name='compile'),
    path('compilev2/', views.send_page, name='sendpage'),
    path('auth/pull/', views.pull_from_github, name="pulley"),
    path('alllocations/', views.addngrams, name='alllocations'),
    path('registered-agents/', views.get_registered_agents, name='registered_agents_search'),
    path('login/', views.login, name='login'),
    path('auth/manage/', views.manage, name='manage'),
    path('auth/site/create/', views.create_site, name='site_create'),
    path('auth/site/update/', views.update_nice, name='site_update'),
    path('auth/editor/update/', views.update_editor, name='editor_update'),
    path('auth/template/create/', views.create_template, name='template_create'),
    path('auth/template/update/', views.update_template, name='template_update'),
    path('auth/blog/create/', views.create_blog, name='blog_create'),
    path('auth/blog/update/', views.update_blog, name='blog_update'),
    path('auth/state/create/', views.create_state, name='state_create'),
    path('auth/state/update/', views.update_state, name='state_update'),
    path('auth/county/create/', views.create_county, name='county_create'),
    path('auth/county/update/', views.update_county, name='county_update'),
    path('auth/city/create/', views.create_city, name='city_create'),
    path('auth/city/update/', views.update_city, name='city_update'),
    path('auth/nice/update/', views.update_site, name='nice_update'),
    path('auth/code/update/', views.update_code, name='code_update'),
    path('auth/db/json/<str:collection>/', views.ret_jason, name='get_json_from_db'),
    # path('auth/db/json/', views.create_telecoms, name='get_json_from_db'),
    path('admin/', admin.site.urls),
    path('auth/upload/', views.upload_file, name='file_upload'),
    path('auth/db-sync/', views.home, name='json_to_mongo'),
    path('__debug__/', include(debug_toolbar.urls)),
] + static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
