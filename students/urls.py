from django.urls import path

from students.views import (
    StudentDetailView,
    StudentFacePhotoUpdateView,
    StudentFacePhotosListView,
    StudentListCreateView,
)

urlpatterns = [
    path('', StudentListCreateView.as_view(), name='student-list-create'),
    path('<int:pk>/', StudentDetailView.as_view(), name='student-detail'),
    path('<int:pk>/face-photo/', StudentFacePhotoUpdateView.as_view(), name='student-face-photo'),
    path('face-photos/', StudentFacePhotosListView.as_view(), name='student-face-photos'),
]
