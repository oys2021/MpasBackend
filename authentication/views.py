from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import User, StudentProfile,AdminProfile
from datetime import datetime, time
from django.utils.timezone import now, make_aware
from authentication.utils import send_email_notification 

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    StudentProfileSerializer,
    AdminProfileSerializer,StudentDetailSerializer,AdminDetailSerializer
)



@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        raw_password = request.data.get('password')  # Get raw password from request

        # subject = 'Your GCTU Student Account Details'
        # html_content = f"""
        # <p>Hello <strong>{user.full_name}</strong>,</p>
        # <p>Your student portal account has been created.</p>
        # <p><strong>Login Details:</strong><br>
        # Student ID: {user.student_id}<br>
        # PIN (Password): <strong>{raw_password}</strong></p>
        # <p>Please keep this information safe. Contact administration if you need to change your PIN.</p>
        # <p>Best regards,<br>GCTU Admin Team</p>
        # """

        # send_email_notification(user.email, subject, html_content)

        return Response({
            'message': 'User registered successfully. Email sent.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    print("Registration failed with errors:", serializer.errors)

    return Response({
        "message": "Registration failed",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)






@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful.',
            'tokens': tokens,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    user_data = UserSerializer(user).data
    if user.role == 'student' and hasattr(user, 'student_profile'):
        user_data['student_profile'] = StudentProfileSerializer(user.student_profile).data
    elif user.role == 'admin' and hasattr(user, 'admin_profile'):
        user_data['admin_profile'] = AdminProfileSerializer(user.admin_profile).data

    return Response(user_data, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_stats(request):
    today = now()
    start_of_month = make_aware(datetime.combine(today.replace(day=1), time.min))
    
    total_students = User.objects.filter(role='student').count()
    total_active_students = StudentProfile.objects.filter(status='active').count()
    total_inactive_students = StudentProfile.objects.filter(status='inactive').count()
    new_students_this_month = User.objects.filter(
        role='student',
        created_at__gte=start_of_month
    ).count()

    return Response({
        "total_students": total_students,
        "total_active_students": total_active_students,
        "total_inactive_students":total_inactive_students,
        "new_students_this_month": new_students_this_month,
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_students(request):
    students = User.objects.filter(role='student').select_related('student_profile')
    serializer = StudentDetailSerializer(students, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_all_admins(request):
    students = User.objects.filter(role='admin').select_related('admin_profile')
    serializer = AdminDetailSerializer(students, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_student(request, student_id):
    try:
        user = User.objects.get(student_id=student_id, role='student')
    except User.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)

    serializer = UserRegistrationSerializer(user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_admin(request, email):
    try:
        user = User.objects.get(email=email, role='admin')
    except User.DoesNotExist:
        return Response({"error": "Admin not found"}, status=404)

    serializer = UserRegistrationSerializer(user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):
    today = now()
    start_of_month = make_aware(datetime.combine(today.replace(day=1), time.min))
    
    total_admin = User.objects.filter(role='admin').count()
    total_active_admin = AdminProfile.objects.filter(status='active').count()
    total_inactive_admin = AdminProfile.objects.filter(status='inactive').count()
    new_admin_this_month = User.objects.filter(
        role='admin',
        created_at__gte=start_of_month
    ).count()

    return Response({
        "total_admin": total_admin,
        "total_active_admin": total_active_admin,
        "total_inactive_admin":total_inactive_admin,
        "new_admin_this_month": new_admin_this_month,
    })