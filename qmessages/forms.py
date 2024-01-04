
from django import forms
from qmessages.models import Message, MessageReply, Note
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)
    receiver = forms.ModelChoiceField(queryset=User.objects.none())  # Empty queryset

    class Meta:
        model = Message
        fields = ['project', 'app', 'model', 'receiver', 'subject', 'text']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(MessageForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['receiver'].queryset = User.objects.exclude(id=self.user.id)

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text:
            raise forms.ValidationError('This field cannot be blank.')
        return text

    def save(self, commit=True):
        instance = super(MessageForm, self).save(commit=False)
        instance.sender = self.user
        if commit:
            instance.save()
        return instance

class MessageReplyForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = MessageReply
        fields = ['text']

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text:
            raise forms.ValidationError('This field cannot be blank.')
        return text

class NoteForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Note
        fields = ['project', 'app', 'model', 'text']

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text:
            raise forms.ValidationError('This field cannot be blank.')
        return text