from django.urls import path
from .views import register_user,update_admin,dashboard_stats,forgot_password,reset_password,login_user,list_all_admins,admin_stats, user_profile,student_stats,list_all_students,update_student
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('profile/', user_profile, name='profile'),
    path('student-stats/', student_stats, name='student-stats'),
    path('admin-stats/', admin_stats, name='admin-stats'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('students/', list_all_students, name='list-all-students'),
    path('admins/', list_all_admins, name='list-all-admins'),
    path("students/<str:student_id>/", update_student),
    path("admins/<str:email>/", update_admin),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('forgot-password/',forgot_password, name='forgot_password'),
    path('reset-password/',reset_password, name='reset_password'),
]
