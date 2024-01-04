=====
QMessages
=====

QMessages is a Django app to conduct web-based messages.

A Message instance is created with the sender and receiver fields set to the email addresses of the users involved in the conversation.

A MessageContent instance is created for each message sent or received. 

The message field of MessageContent is set to the Message instance, and the text field is set to the content of the message.

Each time a message is sent or received, a MessageStatus instance can be created to track the status of the message (read, unread, replied). 

The message field of MessageStatus is set to the Message instance, and the message_desc field is set to the appropriate MessageStatusDesc instance.

Quick start
-----------

1. Add "QMessages" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "QMessages",
    ]

2. Include the docs URLconf in your project urls.py like this::

    path("messages/", include("qmessages.urls")),

3. Run ``python manage.py migrate`` to create the QMessages models.
