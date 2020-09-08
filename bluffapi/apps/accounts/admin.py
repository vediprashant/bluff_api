from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User

admin.site.register(User)
admin.site.unregister(Group)
