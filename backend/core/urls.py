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
    path('api/auth/me/', views.me, name='me'),

    # Chat
    path('api/chat/', views.chat_endpoint, name='chat_endpoint'),
    path('api/chat/stream/', views.chat_stream_endpoint, name='chat_stream_endpoint'),

    # Sessions
    path('api/sessions/', views.list_sessions, name='list_sessions'),
    path('api/session/', views.create_session, name='create_session'),
    path('api/session/<uuid:session_id>/', views.get_session, name='get_session'),

    # Message feedback
    path('api/messages/<int:message_id>/feedback/', views.message_feedback, name='message_feedback'),

    # Documents
    path('api/documents/upload/', views.upload_documents, name='upload_documents'),

    # Admin
    path('api/admin/stats/', views.admin_stats, name='admin_stats'),
    path('api/admin/users/', views.admin_users, name='admin_users'),
    path('api/admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('api/admin/documents/', views.admin_documents, name='admin_documents'),
    path('api/admin/documents/<str:doc_name>/', views.admin_document_delete, name='admin_document_delete'),
    path('api/admin/eval-results/', views.admin_eval_results, name='admin_eval_results'),
    path('api/admin/eval-report/', views.admin_eval_report_pdf, name='admin_eval_report_pdf'),
]
