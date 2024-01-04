import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class BaseModel(models.Model):
    deleted = models.BooleanField(default=False)
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self):
        self.deleted = True
        self.save()
    
    def hard_delete(self):
        super().delete()

class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)
   
class Message(BaseModel):
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    project = models.CharField(max_length=255, null=True)
    app = models.CharField(max_length=255, null=True)
    model = models.CharField(max_length=255, null=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="message_sender", on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="message_receiver", on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    objects = BaseModelManager()

  
    def __str__(self):
        return f"{self.subject} - {str(self.token)}"

class MessageStatusDesc(models.Model):
    desc = models.CharField(_("desc"), max_length=255)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    def __str__(self):
        return 'Desc: {}'.format(self.desc)
    
class MessageStatus(models.Model): 
    message_desc = models.ForeignKey(MessageStatusDesc,related_name="messagestatus_messagestatusdesc", verbose_name=_("message desc"), on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name="message_status", verbose_name=_("message"), on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    def __str__(self):
        return 'Message Status: {} - Status Date: {} - Updated On: {}'.format(self.message_desc.desc, self.created_at, self.updated_at)

    def next_status(self):
        status_list = list(MessageStatusDesc.objects.values_list('desc', flat=True))
        current_status_index = status_list.index(self.message_desc.desc)
        if current_status_index < len(status_list) - 1:
            next_status_desc = status_list[current_status_index + 1]
            next_status = MessageStatusDesc.objects.get(desc=next_status_desc)
            self.message_desc = next_status
            self.save()

class MessageReply(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    parent_reply = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    replier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    objects = BaseModelManager()

    def delete(self):
        children = MessageReply.objects.filter(parent_reply=self)
        for child in children:
            child.delete()
        super().delete()

    def hard_delete(self):
        MessageReply.objects.filter(parent_reply=self).delete()
        super().hard_delete()

    def __str__(self):
        return f"Id: {self.id} {self.text} - {str(self.message.token)}"

class MessageReplyStatus(models.Model): 
    message_desc = models.ForeignKey(MessageStatusDesc,related_name="messagereplystatus_messagestatusdesc", verbose_name=_("message desc"), on_delete=models.CASCADE)
    message_reply = models.ForeignKey(MessageReply, related_name="message_reply_status", verbose_name=_("message reply"), on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    def __str__(self):
        return 'Message Status: {} - Status Date: {} - Updated On: {}'.format(self.message_desc.desc, self.created_at, self.updated_at)

    def next_status(self):
        status_list = list(MessageStatusDesc.objects.values_list('desc', flat=True))
        current_status_index = status_list.index(self.message_desc.desc)
        if current_status_index < len(status_list) - 1:
            next_status_desc = status_list[current_status_index + 1]
            next_status = MessageStatusDesc.objects.get(desc=next_status_desc)
            self.message_desc = next_status
            self.save()

class Note(BaseModel):
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    project = models.CharField(max_length=255, null=True)
    app = models.CharField(max_length=255, null=True)
    model = models.CharField(max_length=255, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    objects = BaseModelManager()

    def __str__(self):
        return f"{self.text[:50]} - {str(self.token)}"