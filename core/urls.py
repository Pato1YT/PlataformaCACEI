from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    #editar perfil
    #charco
    path('perfil/', views.editar_perfil, name='perfil'),
    
    #charco
    

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
    path('usuarios/importar/', views.importar_docentes, name='importar_docentes'),

    #docentes
    path('usuarios/<int:pk>/editar/', views.editar_usuario_docente, name='editar_usuario_docente'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario_docente, name='eliminar_usuario_docente'),
    #charco 
    
    path('aviso-privacidad/', views.aviso_privacidad, name='aviso_privacidad'),
    
    # Consumir el EXCEL (chano)
    path('materias/importar/', views.importar_materias, name='importar_materias'),
    
    # Cursos / carga académica
    path('cursos/', views.lista_cursos, name='lista_cursos'),
    path('cursos/nuevo/', views.crear_curso, name='crear_curso'),
    path('cursos/<int:pk>/editar/', views.editar_curso, name='editar_curso'),
    path('cursos/<int:pk>/eliminar/', views.eliminar_curso, name='eliminar_curso'),
    path('cursos/importar/', views.importar_cursos, name='importar_cursos'),

    # Periodos
    path('periodos/nuevo/', views.crear_periodo, name='crear_periodo'),
    path('periodos/<int:pk>/editar/', views.editar_periodo, name='editar_periodo'),
    
    
]