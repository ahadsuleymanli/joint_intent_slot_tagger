from django.urls import path

from . import views

app_name = 'submit_intents'
urlpatterns = [
    path('', views.index, name='index'),
    path('view/', views.view, name='view'),
    path('edit_intents/', views.edit_intents, name='edit_intents'),
]