from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)


class UserManager(BaseUserManager):
    '''
    User Manager for creating users and superusers
    '''
    def create_user(self, email, password=None, **kwargs):
        '''
        Creates and saves a user with given email, name and password
        '''
        if not email:
            raise ValueError('User must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        '''
        Creates and saves a superuser with the given email and password.
        '''
        kwargs['is_superuser'] = True
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )
        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''
    User model for player
    '''
    email = models.EmailField(
        max_length=255,
        unique=True,
        help_text='Email address'
    )
    name = models.CharField(
        max_length=255,
        help_text='Name'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    @property
    def is_staff(self):
        '''
        Returns True if is_superuser is True
        '''
        if self.is_superuser:
            return True
        else:
            return False

    def get_full_name(self):
        '''
        Returns Full Name of user i.e name
        '''
        return self.name

    def get_short_name(self):
        '''
        Returns Short name of user i.e name
        '''
        return self.name

    def __str__(self):
        return self.email
