from celery.decorators import task
from celery.utils.log import get_task_logger
from time import sleep
from django.core.mail import send_mail
logger = get_task_logger(__name__)


@task(name='send_signup_mail')
def send_signup_mail(subject, message, email_from, recipient_list):
    send_mail(subject, message, email_from, recipient_list)
    return('Signup Mail send')


@task(name='send_invite_mail')
def send_invite_mail(subject, message, email_from, recipient_list):
    send_mail(subject, message, email_from, recipient_list)
    return('Invite Mail send')
