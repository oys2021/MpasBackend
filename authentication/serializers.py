from rest_framework import serializers
from authentication.models import User,StudentProfile,AdminProfile

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['program', 'level', 'status']

    def validate_status(self, value):
        if value not in ['active', 'inactive']:
            raise serializers.ValidationError("Status must be either 'active' or 'inactive'.")
        return value



class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = ['department', 'role_description']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'student_id', 'role', 'phone_number', 'created_at']
        read_only_fields = ['id', 'created_at']



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    student_profile = StudentProfileSerializer(required=False)
    admin_profile = AdminProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'student_id', 'phone_number',
            'password', 'role', 'student_profile', 'admin_profile'
        ]

    def validate(self, data):
        role = data.get('role')
        email = data.get('email')
        student_id = data.get('student_id')

        if role == 'student' and not student_id:
            raise serializers.ValidationError("Student ID is required for student accounts.")
        if role != 'student' and not email:
            raise serializers.ValidationError("Email is required for admin accounts.")
        return data

    def create(self, validated_data):
        student_profile_data = validated_data.pop('student_profile', None)
        admin_profile_data = validated_data.pop('admin_profile', None)
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()


        if user.role == 'student' and student_profile_data:
            StudentProfile.objects.create(user=user, **student_profile_data)
        elif user.role == 'admin' and admin_profile_data:
            AdminProfile.objects.create(user=user, **admin_profile_data)

        return user




class UserLoginSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    username = serializers.CharField()  
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate

        user = authenticate(
            request=self.context.get('request'),
            username=data['username'],
            password=data['password'],
            role=data['role']
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data['user'] = user
        return data
