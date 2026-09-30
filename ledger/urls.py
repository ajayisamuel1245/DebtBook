from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/add/', views.customer_add_view, name='customer_add'),
    path('customers/<int:pk>/edit/', views.customer_edit_view, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete_view, name='customer_delete'),
    path('transactions/add/<str:entry_type>/', views.transaction_add_view, name='transaction_add'),
    path('customers/<int:pk>/', views.customer_detail_view, name='customer_detail'),
    path('statement/<uuid:token>/', views.customer_statement_view, name='customer_statement'),
    path('reports/', views.monthly_summary_view, name='monthly_summary'),
    path('statements/', views.statement_directory_view, name='statement_directory'),
]