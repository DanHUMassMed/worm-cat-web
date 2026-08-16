from celery import Celery

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def send_async_email(email_data):
    message = construct_message_with_html(subject=email_data['subject'],
                                          sender="dan@none.com",
                                          receiver=email_data['to'],
                                          message_text=email_data['body'])
    send_message_ssl("dan@none.com", email_data['to'], message)

