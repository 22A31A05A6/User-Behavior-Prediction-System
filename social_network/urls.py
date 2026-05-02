"""social_network URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from admins import views as admin_views
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', admin_views.home, name='home'),
    path('admin_login', admin_views.admin_login, name='admin_login'),
    path('register', user_views.register, name='register'),
    path('admin_home', admin_views.admin_home, name='admin_home'),
    path('user_login', user_views.user_login, name='user_login'),
    path('view_users/',admin_views.view_users,name='view_users'),
    path('view_posts/', admin_views.view_posts, name='view_posts'),
    path('view_videos/',admin_views.view_videos,name='view_videos'),
    path('user_intention/', admin_views.view_user_intention, name='user_intention'),
    path('admin_logout/',admin_views.admin_logout,name='admin_logout'),  
    path('authorize/<str:username>/', admin_views.authorize_user, name='authorize_user'),
    path('unauthorize/<str:username>/', admin_views.unauthorize_user, name='unauthorize_user'),
    path("admin-posts/", admin_views.view_posts, name="admin_view_posts"),
    path('admin-videos/', admin_views.view_videos, name='admin_view_videos'),
    path('play-video/<int:id>/', admin_views.play_video, name='play_video'),
    path('admin-intention/',admin_views.view_user_intention,name='admin_view_user_intention'),
    path('user/home/', user_views.user_home, name='user_home'),
    path('user_logout/',user_views.user_logout,name='logout'),
    path('search/', user_views.search_friends, name='search_friends'),
    path('friend/<str:username>/', user_views.friend_details, name='friend_details'),
    path('friend-requests/', user_views.view_friend_requests, name='view_friend_requests'),
    path('accept-request/<int:id>/', user_views.accept_request, name='accept_request'),
    path('upload-post/', user_views.upload_post, name='upload_post'),
    path('send-message/', user_views.send_message, name='send_message'),
    path('view-messages/', user_views.view_messages, name='view_messages'),
    path('create-group/', user_views.create_group, name='create_group'),
    path('view-posts/', user_views.view_posts, name='user_view_posts'),
    path('add-comment/', user_views.add_comment, name='add_comment'),
    path("add-friends/", user_views.add_friends, name="add_friends"),
    path("view-group-request/", user_views.view_group_requests, name="view_group_request"),
    path("accept-group/<int:id>/", user_views.accept_group_request, name="accept_group"),
    path("view-group-members/", user_views.view_group_members, name="view_group_members"),
    path("upload-video/", user_views.upload_video, name="upload_video"),
    path("view-videos/", user_views.view_videos, name="view_videos"),
    path('admin_user_intention/', admin_views.admin_view_user_intention, name='admin_view_user_intention')
     
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


