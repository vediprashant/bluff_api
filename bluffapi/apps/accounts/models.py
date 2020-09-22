from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None,):
        '''
        Creates and saves a user with given email, name and password
        '''
        if not email:
            raise ValueError('User must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            # admin=admin,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        '''
        Creates and saves a superuser with the given email and password.
        '''
        user = self.create_user(
            email,
            password=password,
        )
        return user


class User(AbstractBaseUser):
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
        blank=False,
        help_text='Name'
    )
<<<<<<< HEAD
    admin = models.BooleanField(default=False)

=======
    
>>>>>>> origin/nk_task_1
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return True

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):
        return self.email
