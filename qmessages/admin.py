from django.contrib import admin
from qmessages.models import Message, MessageStatus, MessageStatusDesc, MessageReply, MessageReplyStatus, Note

# Register your models here.
class MessageReplyAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return MessageReply.all_objects.all()


admin.site.register(Message)
admin.site.register(MessageStatus)
admin.site.register(MessageStatusDesc)
admin.site.register(MessageReply, MessageReplyAdmin)   
admin.site.register(MessageReplyStatus)
admin.site.register(Note)


