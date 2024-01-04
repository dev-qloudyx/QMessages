from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from qmessages.models import Message, MessageStatus, MessageStatusDesc, Note
from qmessages.views import MessageCreateView, MessageStatusUpdateView, NoteCreateView

class NoteCreateViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.view = NoteCreateView.as_view()
    
    def test_get(self):
        request = self.factory.get('/notes/create/')
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        
    
    def test_post_valid_form(self):
        request = self.factory.post('/notes/create/', data={
            'project': 'Test Project',
            'app': 'Test App',
            'model': 'Test Model',
            'text': 'Test Text',
        })
        request.user = self.user
        response = self.view(request)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.first()
        self.assertEqual(note.project, 'Test Project')
        self.assertEqual(note.app, 'Test App')
        self.assertEqual(note.model, 'Test Model')
        self.assertEqual(note.text, 'Test Text')
        self.assertEqual(str(note.token), response['success'])
    
    def test_post_invalid_form(self):
        request = self.factory.post('/notes/create/', data={})
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response['error'], {'project': ['This field is required.'], 'app': ['This field is required.'], 'model': ['This field is required.'], 'text': ['This field is required.']})
        self.assertEqual(Note.objects.count(), 0)

class MessageCreateViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.view = MessageCreateView.as_view()
    
    def test_get(self):
        request = self.factory.get('/message/create/')
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        
    
    def test_post_valid_form(self):
        request = self.factory.post('/message/create/', data={
            'project': 'Test Project',
            'app': 'Test App',
            'model': 'Test Model',
            'sender': 'test_sender@test.com',
            'receiver': 'test_receiver@test.com',
            'subject': 'Test Subject',
            'text': 'Test Text',
        })
        request.user = self.user
        response = self.view(request)
        self.assertEqual(Message.objects.count(), 1)
        message = Message.objects.first()
        self.assertEqual(message.project, 'Test Project')
        self.assertEqual(message.app, 'Test App')
        self.assertEqual(message.model, 'Test Model')
        self.assertEqual(message.sender, 'test_sender@test.com')
        self.assertEqual(message.receiver, 'test_receiver@test.com')
        self.assertEqual(message.subject, 'Test Subject')
        self.assertEqual(message.text, 'Test Text')
        self.assertEqual(str(message.token), response['success'])
    
    def test_post_invalid_form(self):
        request = self.factory.post('/message/create/', data={})
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response['error'], {'project': ['This field is required.'], 'app': ['This field is required.'], 'model': ['This field is required.'], 'sender': ['This field is required.'], 'receiver': ['This field is required.'], 'subject': ['This field is required.'], 'text': ['This field is required.']})
        self.assertEqual(Message.objects.count(), 0)

class MessageStatusUpdateViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        message = Message.objects.create(
            project='Test Project',
            app='Test App',
            model='Test Model',
            sender='test_sender@test.com',
            receiver='test_receiver@test.com',
            subject='Test Subject',
            text='Test Text')
        message.save()
        status_desc = MessageStatusDesc.objects.get(desc='Unread')
        MessageStatus.objects.create(message_desc=status_desc, message=message)
        self.message = message
        self.view = MessageStatusUpdateView.as_view()

    def test_get_with_valid_token(self):
        request = self.factory.get('/message/update/', {'token': {self.message.token}})
        request.user = self.user
        response = self.view(request)
        message_status = self.message.message_status.order_by('-created_on').first()
        self.assertEqual(response['success'], f'Message received a new status: {message_status.message_desc.desc}')
    
    def test_get_with_invalid_token(self):
        request = self.factory.get('/message/update/', {'token': 'invalid_token'})
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response['error'], 'Invalid token')

    def test_post_with_valid_token(self):
        request = self.factory.post('/message/update/', {'token': {self.message.token}})
        request.user = self.user
        response = self.view(request)
        message_status = self.message.message_status.order_by('-created_on').first()
        self.assertEqual(response['success'], f'Message received a new status: {message_status.message_desc.desc}')

    def test_post_with_invalid_token(self):
        request = self.factory.post('/message/update/', {'token': 'invalid_token'})
        request.user = self.user
        response = self.view(request) 
        self.assertEqual(response['error'], 'Invalid token')


    