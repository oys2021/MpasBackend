from django.contrib import admin
from authentication.models import *

admin.site.register(User)
admin.site.register(StudentProfile)
admin.site.register(AdminProfile)

# Register your models here.
