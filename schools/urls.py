from django.urls import path

from schools.views import (
    ClassRoomDetailView,
    ClassRoomListCreateView,
    SchoolDetailView,
    SchoolListCreateView,
)

urlpatterns = [
    path('', SchoolListCreateView.as_view(), name='school-list-create'),
    path('<int:pk>/', SchoolDetailView.as_view(), name='school-detail'),
    path('classrooms/', ClassRoomListCreateView.as_view(), name='classroom-list-create'),
    path('classrooms/<int:pk>/', ClassRoomDetailView.as_view(), name='classroom-detail'),
]
