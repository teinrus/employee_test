from django.urls import path
from . import views
from .views import pdf_results

urlpatterns = [
    path('', views.select_direction, name='select_direction'),
    path('test/<int:direction_id>/', views.test_view, name='test_view'),
    path('enter_surname/', views.enter_surname, name='enter_surname'),
    path('results/<int:result_id>/', views.test_results, name='test_results'),

    path('pdf_results/<int:result_id>/', pdf_results, name='pdf_results'),


]
