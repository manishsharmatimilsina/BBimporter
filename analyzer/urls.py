from django.urls import path
from . import views

app_name = 'analyzer'
urlpatterns = [
    path('', views.home, name='home'),
    path('download/', views.download_results, name='download_results'),
]
