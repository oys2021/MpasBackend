from django.contrib.auth.backends import BaseBackend
from .models import User

class StudentAdminAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Try student login
        user = None

        if 'role' in kwargs and kwargs['role'] == 'student':
            try:
                user = User.objects.get(student_id=username, role='student')
            except User.DoesNotExist:
                return None

        elif 'role' in kwargs and kwargs['role'].startswith('admin'):
            try:
                user = User.objects.get(email=username, role=kwargs['role'])
            except User.DoesNotExist:
                return None

        if user and user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
