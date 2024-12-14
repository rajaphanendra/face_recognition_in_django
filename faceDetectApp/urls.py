from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Main index page
    path('info/', views.info, name='info'),  # User registration
    path('process-frame/', views.process_frame, name='process_frame'),  # Process frame
    path('face-recognition/', views.face_recognition_view, name='face_recognition'),  # Face recognition
    path('attendance/', views.attendance, name='attendance'),  # Attendance page
]
