from rest_framework import serializers
from authentication.models import User,StudentProfile,AdminProfile

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['program', 'level', 'status']
    
    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in StudentProfile.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Status must be either 'active' or 'inactive'.")
        return value


class StudentDetailSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'student_id',
            'phone_number', 'created_at', 'student_profile'
        ]



class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = ['department', 'role_description','status']
    
    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in AdminProfile.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Status must be either 'active' or 'inactive'.")
        return value


class AdminDetailSerializer(serializers.ModelSerializer):
    admin_profile = AdminProfileSerializer()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email',
            'phone_number', 'created_at', 'admin_profile'
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'student_id', 'role', 'phone_number', 'created_at']
        read_only_fields = ['id', 'created_at']



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    student_profile = StudentProfileSerializer(required=False)
    admin_profile = AdminProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'student_id', 'phone_number',
            'password', 'role', 'student_profile', 'admin_profile'
        ]

    def validate(self, data):
        role = data.get('role', self.instance.role if self.instance else None)
        email = data.get('email', self.instance.email if self.instance else None)
        student_id = data.get('student_id', self.instance.student_id if self.instance else None)

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

        user.raw_password = password

        if user.role == 'student' and student_profile_data:
            StudentProfile.objects.create(user=user, **student_profile_data)
        elif user.role == 'admin' and admin_profile_data:
            AdminProfile.objects.create(user=user, **admin_profile_data)

        return user

    def update(self, instance, validated_data):
        student_profile_data = validated_data.pop('student_profile', None)
        admin_profile_data = validated_data.pop('admin_profile', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if instance.role == 'student' and student_profile_data:
            profile, _ = StudentProfile.objects.get_or_create(user=instance)
            for attr, value in student_profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        if instance.role == 'admin' and admin_profile_data:
            profile, _ = AdminProfile.objects.get_or_create(user=instance)
            for attr, value in admin_profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance





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
