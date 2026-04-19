# =============================================================================
# IMPORTS
# =============================================================================

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'core'


# =============================================================================
# URL PATTERNS
# =============================================================================
#
# Orden de secciones (mismo que views.py y forms.py):
#   1. General       — dashboard, perfil, páginas estáticas
#   2. Autenticación — login, logout
#   3. Atributos de egreso
#   4. Materias
#   5. Usuarios / Docentes
#   6. Periodos
#   7. Cursos
#
# IMPORTANTE: dentro de cada sección, las rutas estáticas van SIEMPRE antes
# que las rutas con parámetros (<int:pk>), porque Django evalúa de arriba
# a abajo y un segmento como "importar" podría ser capturado erróneamente
# por <int:pk> si la ruta estática aparece después.
#
# =============================================================================

urlpatterns = [

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------
    path('',                  views.dashboard,      name='dashboard'),
    path('perfil/',           views.editar_perfil,  name='perfil'),
    path('aviso-privacidad/', views.aviso_privacidad, name='aviso_privacidad'),

    # -------------------------------------------------------------------------
    # Autenticación
    # -------------------------------------------------------------------------
    path('login/',  auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'),         name='logout'),

    # -------------------------------------------------------------------------
    # Atributos de egreso
    # -------------------------------------------------------------------------
    path('atributos/',                      views.lista_atributos,   name='lista_atributos'),
    path('atributos/nuevo/',                views.crear_atributo,    name='crear_atributo'),
    path('atributos/<int:pk>/editar/',      views.editar_atributo,   name='editar_atributo'),
    path('atributos/<int:pk>/eliminar/',    views.eliminar_atributo, name='eliminar_atributo'),

    # -------------------------------------------------------------------------
    # Materias
    # -------------------------------------------------------------------------
    path('materias/',                       views.lista_materias,    name='lista_materias'),
    path('materias/nueva/',                 views.crear_materia,     name='crear_materia'),
    path('materias/importar/',              views.importar_materias, name='importar_materias'),  # antes de <pk>
    path('materias/<int:pk>/editar/',       views.editar_materia,    name='editar_materia'),
    path('materias/<int:pk>/eliminar/',     views.eliminar_materia,  name='eliminar_materia'),

    # -------------------------------------------------------------------------
    # Usuarios / Docentes
    # -------------------------------------------------------------------------
    path('usuarios/',                       views.lista_usuarios,           name='lista_usuarios'),
    path('usuarios/nuevo-docente/',         views.crear_usuario_docente,    name='crear_usuario_docente'),
    path('usuarios/importar/',              views.importar_docentes,        name='importar_docentes'),  # antes de <pk>
    path('usuarios/<int:pk>/editar/',       views.editar_usuario_docente,   name='editar_usuario_docente'),
    path('usuarios/<int:pk>/eliminar/',     views.eliminar_usuario_docente, name='eliminar_usuario_docente'),

    # -------------------------------------------------------------------------
    # Periodos
    # -------------------------------------------------------------------------
    path('periodos/',                       views.lista_periodos,   name='lista_periodos'),
    path('periodos/nuevo/',                 views.crear_periodo,    name='crear_periodo'),
    path('periodos/<int:pk>/editar/',       views.editar_periodo,   name='editar_periodo'),
    path('periodos/<int:pk>/eliminar/',     views.eliminar_periodo, name='eliminar_periodo'),

    # -------------------------------------------------------------------------
    # Cursos
    # -------------------------------------------------------------------------
    path('cursos/',                         views.lista_cursos,    name='lista_cursos'),
    path('cursos/nuevo/',                   views.crear_curso,     name='crear_curso'),
    path('cursos/importar/',                views.importar_cursos, name='importar_cursos'),  # antes de <pk>
    path('cursos/<int:pk>/editar/',         views.editar_curso,    name='editar_curso'),
    path('cursos/<int:pk>/eliminar/',       views.eliminar_curso,  name='eliminar_curso'),

]