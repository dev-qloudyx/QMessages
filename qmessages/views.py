

# Django
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import HttpResponse, JsonResponse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models import Q

# Qmessages
from qmessages.forms import MessageForm, MessageReplyForm, NoteForm
from qmessages.models import Message, MessageReply, MessageReplyStatus, MessageStatus, MessageStatusDesc, Note
from qmessages.utils import check_token, get_filters_from_request


# Messages

class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_create.html'
    base_template = "base.html"

    def get_success_url(self):
        return reverse('qmessages:message_list_view')
    
    def get_form_kwargs(self):
        kwargs = super(MessageCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = self.base_template
        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.project = self.kwargs.get('project') or self.request.POST.get('project')
        self.object.app = self.kwargs.get('app') or self.request.POST.get('app')
        self.object.model = self.kwargs.get('model') or self.request.POST.get('model')
        self.object.save()
        status_desc = MessageStatusDesc.objects.get(desc='Unread')
        MessageStatus.objects.create(message_desc=status_desc, message=self.object)
        if self.request.is_ajax:
            return {"success": str(self.object.token)}
        else:
            super().form_valid(form)
            return {"success": str(self.object.token)}

    def form_invalid(self, form):
        return {"error": form.errors}

    def render_to_response(self, context, **response_kwargs):
        return super().render_to_response(context, **response_kwargs)

class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_update.html'
    base_template = "base.html"
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get_success_url(self):
        return reverse('qmessages:message_list_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = self.base_template
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        if self.request.is_ajax:
            return JsonResponse({"success": str(self.object.token)}, safe=False)
        else:
            return super().form_valid(form)

    def form_invalid(self, form):
        return JsonResponse({"error": form.errors}, safe=False)

    def render_to_response(self, context, **response_kwargs):
        if self.request.user == self.object.sender:
            return super().render_to_response(context, **response_kwargs)
        else:
            if self.request.is_ajax:
                return JsonResponse({"error": "You are not the owner of this message"}, safe=False)
            else:
                return HttpResponse("You are not the owner of this message")
            
class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    form_class = MessageForm
    template_name = 'message_detail.html'
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get_object(self):
        token = self.kwargs.get('token', None) or self.request.GET.get('token', None)
        uuid_token = check_token([token])
        return Message.objects.get(token=uuid_token[0])

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax:
            message_data_dict = model_to_dict(self.object)
            message_data_dict['token'] = str(self.object.token)
            return JsonResponse(message_data_dict, safe=False)
        else:
            return super().render_to_response(context, **response_kwargs)

class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    paginate_by = 5
    max_paginate_by = 100

    def get_paginate_by(self, queryset):
        if 'pageSize' not in self.request.GET:
            self.paginate_by = self.max_paginate_by
            return self.paginate_by
        return self.request.GET.get('pageSize', self.paginate_by)
    
    def get_queryset(self, request, *args, **kwargs):
        uuid_tokens = check_token(self.tokens)
        queryset = Message.objects.filter(
            Q(token__in=uuid_tokens) & (Q(sender=self.request.user) | Q(receiver=self.request.user))
        ).order_by('-created_at')
        
        if request.is_ajax:
            if 'filter[filters][0][field]' in request.GET:
                filters = get_filters_from_request(request)
                new_filters = {}
                operation = 'filter'
                for k, v in filters.items():
                    if 'exclude_' in k:
                        operation = 'exclude'
                        new_filters[k.replace('exclude_', '')] = v
                    else:
                        new_filters[k] = v

                if operation == 'exclude':
                    queryset = queryset.exclude(**new_filters)
                else:
                    queryset = queryset.filter(**new_filters)
                
            return queryset
        else:
            return queryset
    
    def get(self, request, *args, **kwargs):
        self.tokens = kwargs.get('tokens', None) or request.GET.get('tokens', None)
        self.object_list = self.get_queryset(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)

        if request.is_ajax:
            if not context['page_obj'].object_list.exists():
                return JsonResponse({"error": 'No data found for this token'}, status=404)

            message_data_list = []

            for message in context['page_obj']:
                message_dict = model_to_dict(message)
                message_dict['token'] = str(message.token)
                message_dict['sender'] = message.sender.email
                message_dict['created_at'] = message.created_at
                message_dict['updated_at'] = message.updated_at

                # Get the latest status of the message
                message_status = MessageStatus.objects.filter(message=message).order_by('-created_at').first()
                if message_status:
                    message_dict['status'] = message_status.message_desc.desc

                top_level_replies = MessageReply.objects.filter(message=message, parent_reply__isnull=True)
                reply_list = []

                for reply in top_level_replies:
                    reply_dict = model_to_dict(reply)
                    reply_dict['created_at'] = reply.created_at
                    reply_dict['updated_at'] = reply.updated_at
                    reply_dict['replier'] = reply.replier.email

                    # Get the latest status of the reply
                    reply_status = MessageReplyStatus.objects.filter(message_reply=reply).order_by('-created_at').first()
                    if reply_status:
                        reply_dict['status'] = reply_status.message_desc.desc

                    nested_replies = MessageReply.objects.filter(parent_reply=reply)
                    nested_reply_list = []

                    for nested_reply in nested_replies:
                        nested_reply_dict = model_to_dict(nested_reply)
                        nested_reply_dict['created_at'] = nested_reply.created_at
                        nested_reply_dict['updated_at'] = nested_reply.updated_at
                        nested_reply_dict['replier'] = nested_reply.replier.email

                        # Get the latest status of the nested reply
                        nested_reply_status = MessageReplyStatus.objects.filter(message_reply=nested_reply).order_by('-created_at').first()
                        if nested_reply_status:
                            nested_reply_dict['status'] = nested_reply_status.message_desc.desc

                        nested_reply_list.append(nested_reply_dict)

                    reply_dict['replies'] = nested_reply_list
                    reply_list.append(reply_dict)

                message_dict['replies'] = reply_list
                message_data_list.append(message_dict)

            # Convert the flat list to a hierarchical structure
            message_data_dict = {}
            for message_dict in message_data_list:
                message_data_dict[message_dict['id']] = message_dict

            hierarchical_data_list = list(message_data_dict.values())

            data = {
                'data': hierarchical_data_list,
                'pagination': {
                    'page': context['page_obj'].number,
                    'total_pages': context['page_obj'].paginator.num_pages,
                    'has_next': context['page_obj'].has_next(),
                    'has_previous': context['page_obj'].has_previous(),
                    'count': context['page_obj'].paginator.count,
                }
            }

            return JsonResponse(data, safe=False)

        else:
            return render(request, 'message_list.html', context)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = 'message_delete.html'
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get_success_url(self):
        return reverse('qmessages:message_list_view')
    
    def get_object(self, queryset=None):
        token = self.kwargs.get('token', None) or self.request.GET.get('token', None)
        uuid_token = check_token([token])
        return get_object_or_404(Message, token=uuid_token[0])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user == self.object.sender:
            self.object.delete() # Soft delete
            # self.object.hard_delete() # Hard delete
            if self.request.is_ajax:
                return JsonResponse({'success': 'Message deleted successfully'})
            else:
                return super(MessageDeleteView, self).delete(request, *args, **kwargs)
        else:
            if self.request.is_ajax:
                return JsonResponse({"error": "You are not the owner of this message"}, safe=False)
            else:
                return HttpResponse("You are not the owner of this message")
         
class MessageStatusUpdateView(LoginRequiredMixin, View):
    model = Message
    form_class = MessageForm
    base_template = "base.html"
  
    def get_context_data(self, **kwargs):
        context = {'base_template': self.base_template}
        return context

    def post(self, request, *args, **kwargs):
        token = [request.POST.get('token', None) or kwargs.get('token', None)]
        valid_uuid_token, invalid_uuid_tokens = check_token(token)
        if valid_uuid_token:
            message_data = Message.objects.get(token=valid_uuid_token[0])
            message_status = message_data.message_status.order_by('-created_on').first()
            if not message_data:
                return {'error': 'No data found for this token'}
            if message_status:
                message_status.next_status()
                return {'success': f"Message received a new status: {message_status.message_desc.desc}"}
            else:
                return {'error': 'This message has no status'}
        else:
            return {'error': 'Invalid token'}
        
    def get(self, request, *args, **kwargs):
        token = [kwargs.get('token', None) or request.GET.get('token', None)]
        valid_uuid_token, invalid_uuid_tokens = check_token(token)
        if valid_uuid_token:
            message_data = Message.objects.get(token=valid_uuid_token[0])
            message_status = message_data.message_status.order_by('-created_on').first()
            if not message_data:
                return {'error': 'No data found for this token'}
            if message_status:
                message_status.next_status()
                return {'success': f"Message received a new status: {message_status.message_desc.desc}"}
            else:
                return {'error': 'This message has no status'}
        else:
            return {'error': 'Invalid token'}

class MessageReplyCreateView(LoginRequiredMixin, CreateView):
    model = MessageReply
    form_class = MessageReplyForm
    template_name = 'message_reply_create.html'
    base_template = "base.html"

    def get_success_url(self):
        return reverse('qmessages:message_list_view')
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = self.base_template
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.token = self.kwargs.get('token', None) or self.request.POST.get('token', None)
        uuid_token = check_token([self.token])
        self.object.message = Message.objects.get(token=uuid_token[0])
        parent_reply_id = self.object.parent_reply_id or self.kwargs.get('parent_reply', None) or self.request.POST.get('parent_reply', None)
        
        if parent_reply_id is not None and parent_reply_id != '':
            self.object.parent_reply = MessageReply.objects.get(id=parent_reply_id)
        
        self.object.replier = self.request.user
        self.object.save()
        status_desc_reply = MessageStatusDesc.objects.get(desc='Replied')
        status_desc_unread = MessageStatusDesc.objects.get(desc='Unread')

        if self.object.parent_reply:
            MessageReplyStatus.objects.create(message_desc=status_desc_reply, message_reply=self.object.parent_reply)
            MessageReplyStatus.objects.create(message_desc=status_desc_unread, message_reply=self.object)
        else:
            MessageStatus.objects.create(message_desc=status_desc_unread, message=self.object.message)
            MessageReplyStatus.objects.create(message_desc=status_desc_unread, message_reply=self.object)
        
        if MessageStatus.objects.filter(message=self.object.message).order_by('-created_at').first().message_desc.desc == 'Unread':
            MessageStatus.objects.create(message=self.object.message, message_desc=status_desc_reply)
        else:
            MessageStatus.objects.create(message=self.object.message, message_desc=status_desc_unread)

        if self.request.is_ajax:
            return JsonResponse({"success": str(self.object.token)}, safe=False)
        else:
            return super().form_valid(form)

    def form_invalid(self, form):
        return JsonResponse({"error": form.errors}, safe=False)

    def render_to_response(self, context, **response_kwargs):
        return super().render_to_response(context, **response_kwargs)

class MessageReplyUpdateView(LoginRequiredMixin, UpdateView):
    model = MessageReply
    form_class = MessageReplyForm
    template_name = 'message_reply_update.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('qmessages:message_list_view')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        if self.request.is_ajax:
            return JsonResponse({"success": str(self.object.pk)}, safe=False)
        else:
            return super().form_valid(form)

    def form_invalid(self, form):
        return JsonResponse({"error": form.errors}, safe=False)

    def render_to_response(self, context, **response_kwargs):
        status_desc_read = MessageStatusDesc.objects.get(desc='Read')
        MessageReplyStatus.objects.create(message_reply=self.object, message_desc=status_desc_read)
        return super().render_to_response(context, **response_kwargs)

class MessageReplyDetailView(LoginRequiredMixin, DetailView):
    model = MessageReply
    form_class = MessageReplyForm
    template_name = 'message_reply_detail.html'
    pk_url_kwarg = 'pk'

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax:
            message_reply_data_dict = model_to_dict(self.object)
            message_reply_data_dict['pk'] = str(self.object.pk)
            return JsonResponse(message_reply_data_dict, safe=False)
        else:
            status_desc_read = MessageStatusDesc.objects.get(desc='Read')
            MessageReplyStatus.objects.create(message_reply=self.object, message_desc=status_desc_read)
            return super().render_to_response(context, **response_kwargs)

class MessageReplyDeleteView(LoginRequiredMixin, DeleteView):
    model = MessageReply
    template_name = 'message_delete.html'

    def get_success_url(self):
        return reverse('qmessages:message_list_view')
    
    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        return get_object_or_404(MessageReply, id=pk)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user == self.object.replier: 
            #self.object.delete() # Soft delete
            self.object.hard_delete() # Hard delete
            if self.request.is_ajax:
                return JsonResponse({'success': 'Message deleted successfully'})
            else:
                return super(MessageReplyDeleteView, self).delete(request, *args, **kwargs)
        else:
            if self.request.is_ajax:
                return JsonResponse({"error": "You are not the owner of this message"}, safe=False)
            else:
                return HttpResponse("You are not the owner of this message")

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

# Notes

class NoteCreateView(LoginRequiredMixin, View):
    model = Note
    form_class = NoteForm
    base_template = "base.html"

    def get_context_data(self, **kwargs):
        context = {'base_template': self.base_template}
        return context
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.project = kwargs.get('project') or request.POST.get('project')
            note.app = kwargs.get('app') or request.POST.get('app')
            note.model = kwargs.get('model') or request.POST.get('model')
            note.save()
            return {"success": str(note.token)}
        return {"error": form.errors}
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = self.form_class()
        return render(request, 'note_create.html', context)