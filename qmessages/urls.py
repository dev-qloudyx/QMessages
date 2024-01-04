from django.urls import path
from qmessages import views

app_name = "qmessages"

urlpatterns = [

    path('message/create/', views.MessageCreateView.as_view(), name='message_create_view'),
    path('message/list/', views.MessageListView.as_view(), name='message_list_view'),
    path('message/detail/', views.MessageDetailView.as_view(), name='message_detail_view'),
    path('message/detail/<str:token>/', views.MessageDetailView.as_view(), name='message_detail_view_with_token'),
    path('message/detail/<str:token>/<int:parent_reply>/', views.MessageDetailView.as_view(), name='message_detail_view_with_token_and_parent_reply'),
    path('message/update/', views.MessageUpdateView.as_view(), name='message_update_view'),
    path('message/update/<str:token>/', views.MessageUpdateView.as_view(), name='message_update_view_with_token'),
    path('message/update/status/', views.MessageStatusUpdateView.as_view(), name='message_status_update_view'),
    path('message/delete/<str:token>/', views.MessageDeleteView.as_view(), name='message_delete_view'),
    path('message/reply/create/', views.MessageReplyCreateView.as_view(), name='message_reply_create_view'),
    path('message/reply/create/<str:token>/', views.MessageReplyCreateView.as_view(), name='message_reply_create_view_with_token'),
    path('message/reply/create/<str:token>/<int:parent_reply>/', views.MessageReplyCreateView.as_view(), name='message_reply_create_view_with_token'),
    path('message/reply/update/<int:pk>/', views.MessageReplyUpdateView.as_view(), name='message_reply_update_view'),
    path('message/reply/detail/<int:pk>/', views.MessageReplyDetailView.as_view(), name='message_reply_detail_view'),
    path('message/reply/delete/<int:pk>/', views.MessageReplyDeleteView.as_view(), name='message_reply_delete_view'),
    path('note/create/', views.NoteCreateView.as_view(), name='note_create_view'),
]