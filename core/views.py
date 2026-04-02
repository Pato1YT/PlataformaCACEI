# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from django.core.exceptions import PermissionDenied
#charco
from django.contrib.auth import update_session_auth_hash

from .models import AtributoEgreso, Materia, Usuario
from .forms import AtributoEgresoForm, MateriaForm, CrearDocenteForm
#charco
from .forms import AtributoEgresoForm, MateriaForm, CrearDocenteForm, EditarPerfilForm




@login_required
def dashboard(request):
    """
    Vista principal del sistema.
    Aquí luego pondremos estadísticas, resúmenes, etc.
    """
    return render(request, 'core/dashboard.html', {'materias': materias})


@login_required
def lista_atributos(request):
    atributos = AtributoEgreso.objects.all().order_by('codigo')
    return render(request, 'atributos/lista_atributos.html', {'atributos': atributos})


@login_required
def crear_atributo(request):
    if request.method == 'POST':
        form = AtributoEgresoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atributo de egreso creado correctamente.')
            return redirect('core:lista_atributos')
    else:
        form = AtributoEgresoForm()

    return render(request, 'atributos/form_atributo.html', {
        'form': form,
        'titulo': 'Crear atributo de egreso'
    })


@login_required
def editar_atributo(request, pk):
    atributo = get_object_or_404(AtributoEgreso, pk=pk)

    if request.method == 'POST':
        form = AtributoEgresoForm(request.POST, instance=atributo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atributo de egreso actualizado correctamente.')
            return redirect('core:lista_atributos')
    else:
        form = AtributoEgresoForm(instance=atributo)

    return render(request, 'atributos/form_atributo.html', {
        'form': form,
        'titulo': 'Editar atributo de egreso'
    })


@login_required
def eliminar_atributo(request, pk):
    atributo = get_object_or_404(AtributoEgreso, pk=pk)

    if request.method == 'POST':
        atributo.delete()
        messages.success(request, 'Atributo de egreso eliminado correctamente.')
        return redirect('core:lista_atributos')

    return render(request, 'atributos/confirmar_eliminar.html', {
        'atributo': atributo
    })
    
    
# =========================
# MATERIAS (RETÍCULA)
# =========================

@login_required
def lista_materias(request):
    materias = Materia.objects.all().order_by('semestre', 'clave')
    return render(request, 'materias/lista_materias.html', {'materias': materias})


@login_required
def crear_materia(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia creada correctamente.')
            return redirect('core:lista_materias')
    else:
        form = MateriaForm()

    return render(request, 'materias/form_materia.html', {
        'form': form,
        'titulo': 'Crear materia',
    })


@login_required
def editar_materia(request, pk):
    materia = get_object_or_404(Materia, pk=pk)

    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada correctamente.')
            return redirect('core:lista_materias')
    else:
        form = MateriaForm(instance=materia)

    return render(request, 'materias/form_materia.html', {
        'form': form,
        'titulo': 'Editar materia',
    })


@login_required
def eliminar_materia(request, pk):
    materia = get_object_or_404(Materia, pk=pk)

    if request.method == 'POST':
        materia.delete()
        messages.success(request, 'Materia eliminada correctamente.')
        return redirect('core:lista_materias')

    return render(request, 'materias/confirmar_eliminar.html', {
        'materia': materia,
    })
    
@login_required
def dashboard(request):
    materias = Materia.objects.all().order_by('semestre', 'clave')
    return render(request, 'core/dashboard.html', {'materias': materias})

def solo_admin(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if request.user.rol != Usuario.ADMINISTRADOR:
            raise PermissionDenied  # 403
        return view_func(request, *args, **kwargs)
    return _wrapped

@solo_admin
def lista_usuarios(request):
    usuarios = Usuario.objects.filter(rol=Usuario.DOCENTE).order_by('-created_at')
    return render(request, 'usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'titulo': 'Usuarios',
    })


@solo_admin
def crear_usuario_docente(request):
    if request.method == 'POST':
        form = CrearDocenteForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']

            # 1) Generamos una contraseña temporal segura
            password_temporal = Usuario.objects.make_random_password()

            # 2) Creamos el usuario como DOCENTE
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password_temporal,
                first_name=first_name,
                last_name=last_name,
                rol=Usuario.DOCENTE,
            )

            # 3) Aviso al admin con las credenciales
            messages.success(
                request,
                f"Docente creado correctamente. "
                f"Usuario: {usuario.username} | Contraseña temporal: {password_temporal}"
            )

            return redirect('core:lista_usuarios')
    else:
        form = CrearDocenteForm()

    return render(request, 'usuarios/form_docente.html', {
        'form': form,
        'titulo': 'Crear docente',
    }) 







@solo_admin
def editar_usuario_docente(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    form = CrearDocenteForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Docente actualizado correctamente.')
        return redirect('core:lista_usuarios')

    return render(request, 'usuarios/form_docente.html', {
        'form': form,
        'titulo': 'Editar docente',
    })


@solo_admin
def eliminar_usuario_docente(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Docente eliminado correctamente.')
        return redirect('core:lista_usuarios')

    return render(request, 'usuarios/confirmar_eliminar.html', {
        'usuario': usuario,
    })
    
    #charco 
@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            usuario = form.save()
            nueva_pass = form.cleaned_data.get('password1')
            if nueva_pass:
                usuario.set_password(nueva_pass)
                usuario.save()
                update_session_auth_hash(request, usuario)
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('core:perfil')
    else:
        form = EditarPerfilForm(instance=request.user)

    return render(request, 'core/perfil.html', {'form': form})

#charco
def aviso_privacidad(request):
    return render(request, 'core/aviso_privacidad.html')