from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Autenticación
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='core:login'
    ), name='logout'),
    
    # Crear Docentes
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo-docente/', views.crear_usuario_docente, name='crear_usuario_docente'),

    # Atributos de Egreso
    path('atributos/', views.lista_atributos, name='lista_atributos'),
    path('atributos/nuevo/', views.crear_atributo, name='crear_atributo'),
    path('atributos/<int:pk>/editar/', views.editar_atributo, name='editar_atributo'),
    path('atributos/<int:pk>/eliminar/', views.eliminar_atributo, name='eliminar_atributo'),
    
     # Materias (CRUD)
    path('materias/', views.lista_materias, name='lista_materias'),
    path('materias/nueva/', views.crear_materia, name='crear_materia'),
    path('materias/<int:pk>/editar/', views.editar_materia, name='editar_materia'),
    path('materias/<int:pk>/eliminar/', views.eliminar_materia, name='eliminar_materia'),

    #docentes
    path('usuarios/<int:pk>/editar/', views.editar_usuario_docente, name='editar_usuario_docente'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario_docente, name='eliminar_usuario_docente'),
]