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

#chano
import os
import json
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .utils.importador_materias import (
    obtener_hojas_excel,
    analizar_hoja_excel,
    ImportadorMateriasError,
)



#@login_required
#def dashboard(request):
    #"""
    #Vista principal del sistema.
    #Aquí luego pondremos estadísticas, resúmenes, etc.
    #"""
    #return render(request, 'core/dashboard.html', {'materias': materias})


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

@login_required
@solo_admin
def importar_materias(request):
    hojas = []
    archivo_temporal = None
    hoja_seleccionada = None
    preview_data = []

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # PASO 1: subir archivo
        if accion == 'subir_archivo':
            archivo = request.FILES.get('archivo_excel')

            if not archivo:
                messages.error(request, 'Debes seleccionar un archivo Excel.')
                return render(request, 'materias/importar_materias.html')

            if not archivo.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'El archivo debe ser Excel (.xlsx o .xls).')
                return render(request, 'materias/importar_materias.html')

            carpeta_temp = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
            os.makedirs(carpeta_temp, exist_ok=True)

            fs = FileSystemStorage(location=carpeta_temp)
            nombre_archivo = fs.save(archivo.name, archivo)
            archivo_temporal = nombre_archivo
            ruta_archivo = fs.path(nombre_archivo)

            try:
                hojas = obtener_hojas_excel(ruta_archivo)
                messages.success(request, 'Archivo cargado correctamente. Ahora selecciona una hoja.')
            except ImportadorMateriasError as e:
                fs.delete(nombre_archivo)
                messages.error(request, str(e))

            return render(request, 'materias/importar_materias.html', {
                'hojas': hojas,
                'archivo_temporal': archivo_temporal,
            })

        # PASO 2: analizar hoja
        elif accion == 'analizar_hoja':
            hoja_seleccionada = request.POST.get('hoja')
            archivo_temporal = request.POST.get('archivo_temporal')

            if not hoja_seleccionada or not archivo_temporal:
                messages.error(request, 'Debes seleccionar una hoja válida.')
                return redirect('core:importar_materias')

            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'temp_imports', archivo_temporal)

            try:
                hojas = obtener_hojas_excel(ruta_archivo)
                preview_data = analizar_hoja_excel(ruta_archivo, hoja_seleccionada)
                messages.success(request, f'Se analizaron {len(preview_data)} materias correctamente.')
            except ImportadorMateriasError as e:
                messages.error(request, str(e))

            return render(request, 'materias/importar_materias.html', {
                'hojas': hojas,
                'archivo_temporal': archivo_temporal,
                'hoja_seleccionada': hoja_seleccionada,
                'preview_data': preview_data,
                'preview_json': json.dumps(preview_data),
            })

        # PASO 3: guardar materias
        elif accion == 'guardar_materias':
            hoja_seleccionada = request.POST.get('hoja')
            archivo_temporal = request.POST.get('archivo_temporal')

            if not hoja_seleccionada or not archivo_temporal:
                messages.error(request, 'No se pudo recuperar la información a guardar.')
                return redirect('core:importar_materias')

            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'temp_imports', archivo_temporal)

            if not os.path.exists(ruta_archivo):
                messages.error(request, 'El archivo temporal ya no existe. Vuelve a cargar el Excel.')
                return redirect('core:importar_materias')

            try:
                preview_data = analizar_hoja_excel(ruta_archivo, hoja_seleccionada)
            except ImportadorMateriasError as e:
                messages.error(request, str(e))
                return redirect('core:importar_materias')

            creadas = 0
            actualizadas = 0

            for fila in preview_data:
                _, created = Materia.objects.update_or_create(
                    clave=fila['clave'],
                    defaults={
                        'nombre': fila['nombre'],
                        'semestre': int(fila['semestre']),
                    }
                )

                if created:
                    creadas += 1
                else:
                    actualizadas += 1

            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

            messages.success(
                request,
                f'Importación completada. Materias creadas: {creadas}. Materias actualizadas: {actualizadas}.'
            )
            return redirect('core:lista_materias')

    return render(request, 'materias/importar_materias.html')

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