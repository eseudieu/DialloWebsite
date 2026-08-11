"""
URL configuration for DialloWebsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

# View imports
from website import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Oauth paths
    path('oauth/', include('social_django.urls', namespace='social')),
    path("oauth-landing", views.oauth_landing, name='oauth-landing'),

    # Main website paths
    path("", views.home_action, name='home'),
    path("login/", views.login_action, name='login'), 
    path("projects", views.projects_action, name='projects'), 
    path("request-service", views.request_service_action, name='request-service'),
    path("view-request/<int:id>", views.view_request_action, name='view-request'),
    path("view-request/pay/<int:id>", views.pay_with_zelle_action, name='pay'),
    path("service-history", views.service_history_action, name='service-history'),
    path("about", views.about_action, name='about'),
    path("logout", views.logout_action, name='logout'),
]
 