from bluffapi.settings.dev import *
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bluff',
        'USER': 'postgres',
        'PASSWORD': 'a12345678',
        'PORT': '',
    }
}