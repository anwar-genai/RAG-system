"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from chat import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('api/auth/register/', views.register_user, name='register'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    # Chat
    path('api/chat/', views.chat_endpoint, name='chat_endpoint'),
    path('api/chat/stream/', views.chat_stream_endpoint, name='chat_stream_endpoint'),
    path('api/documents/upload/', views.upload_documents, name='upload_documents'),
    path('api/session/', views.create_session, name='create_session'),
    path('api/session/<uuid:session_id>/', views.get_session, name='get_session'),
]
