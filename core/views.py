# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from django.core.exceptions import PermissionDenied, ValidationError
#charco
from django.contrib.auth import update_session_auth_hash

from .models import AtributoEgreso, Materia, Usuario, Curso, Periodo
from .forms import AtributoEgresoForm, MateriaForm, CrearDocenteForm, CursoForm
#charco
from .forms import AtributoEgresoForm, MateriaForm, CrearDocenteForm, EditarPerfilForm

from .forms import AtributoEgresoForm, MateriaForm, CrearDocenteForm, CursoForm, PeriodoForm

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

from .utils.importador_docentes import (
    obtener_hojas_excel_docentes,
    analizar_hoja_docentes,
    ImportadorDocentesError,
)

from .utils.importador_cursos import (
    ImportadorCursosError,
    obtener_hojas_excel_cursos,
    analizar_hoja_cursos,
    parsear_periodo_desde_excel,
)

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
    periodo_id = request.session.get('periodo_seleccionado_id')
    periodo_seleccionado = Periodo.objects.filter(pk=periodo_id).first()

    if not periodo_seleccionado:
        periodo_seleccionado = Periodo.objects.filter(es_activo=True).first()

    materias = Materia.objects.none()
    if periodo_seleccionado:
        materias = Materia.objects.filter(
            periodo=periodo_seleccionado
        ).order_by('semestre', 'clave')

    return render(request, 'materias/lista_materias.html', {
        'materias': materias,
        'periodo_seleccionado': periodo_seleccionado,
    })


@login_required
@solo_admin
def crear_materia(request):
    periodo_id = request.session.get('periodo_seleccionado_id')
    periodo_seleccionado = Periodo.objects.filter(pk=periodo_id).first()

    if not periodo_seleccionado:
        periodo_seleccionado = Periodo.objects.filter(es_activo=True).first()

    if not periodo_seleccionado:
        messages.error(request, 'Debes seleccionar o activar un periodo antes de crear una materia.')
        return redirect('core:lista_materias')

    if request.method == 'POST':
        form = MateriaForm(request.POST, periodo=periodo_seleccionado)
        if form.is_valid():
            materia = form.save(commit=False)
            materia.periodo = periodo_seleccionado
            try:
                materia.full_clean()
                materia.save()
                form.save_m2m()
                messages.success(request, 'Materia creada correctamente.')
                return redirect('core:lista_materias')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = MateriaForm(periodo=periodo_seleccionado)

    return render(request, 'materias/form_materia.html', {
        'form': form,
        'titulo': 'Crear materia',
        'periodo_seleccionado': periodo_seleccionado,
    })


@login_required
@solo_admin
def editar_materia(request, pk):
    materia = get_object_or_404(Materia, pk=pk)

    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia, periodo=materia.periodo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Materia actualizada correctamente.')
            return redirect('core:lista_materias')
    else:
        form = MateriaForm(instance=materia, periodo=materia.periodo)

    return render(request, 'materias/form_materia.html', {
        'form': form,
        'titulo': 'Editar materia',
        'periodo_seleccionado': materia.periodo,
    })


@login_required
@solo_admin
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
    periodos = Periodo.objects.all().order_by('-fecha_inicio')

    # Si mandan un periodo_id por GET lo usamos, si no el activo
    periodo_id = request.GET.get('periodo_id')

    if periodo_id:
        periodo_activo = Periodo.objects.filter(pk=periodo_id).first()
        if periodo_activo:
            request.session['periodo_seleccionado_id'] = periodo_activo.id
    else:
        periodo_id_sesion = request.session.get('periodo_seleccionado_id')
        if periodo_id_sesion:
            periodo_activo = Periodo.objects.filter(pk=periodo_id_sesion).first()
        else:
            periodo_activo = Periodo.objects.filter(es_activo=True).first()
            if periodo_activo:
                request.session['periodo_seleccionado_id'] = periodo_activo.id

    cursos = Curso.objects.none()
    if periodo_activo:
        cursos = Curso.objects.filter(
            materia__periodo=periodo_activo
        ).select_related(
            'materia',
            'materia__periodo',
            'docente'
        ).order_by(
            'materia__semestre',
            'materia__clave',
            'grupo'
        )

        if request.user.rol == Usuario.DOCENTE:
            cursos = cursos.filter(docente=request.user)

    return render(request, 'core/dashboard.html', {
        'cursos': cursos,
        'periodo_activo': periodo_activo,
        'periodos': periodos,
    })


@login_required
@solo_admin
def importar_materias(request):
    hojas = []
    archivo_temporal = None
    hoja_seleccionada = None
    preview_data = []

    periodo_id = request.session.get('periodo_seleccionado_id')
    periodo_seleccionado = Periodo.objects.filter(pk=periodo_id).first()

    if not periodo_seleccionado:
        periodo_seleccionado = Periodo.objects.filter(es_activo=True).first()

    if not periodo_seleccionado:
        messages.error(request, 'Debes seleccionar o activar un periodo antes de importar materias.')
        return redirect('core:lista_materias')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # PASO 1: subir archivo
        if accion == 'subir_archivo':
            archivo = request.FILES.get('archivo_excel')

            if not archivo:
                messages.error(request, 'Debes seleccionar un archivo Excel.')
                return render(request, 'materias/importar_materias.html', {
                    'periodo_seleccionado': periodo_seleccionado,
                })

            if not archivo.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'El archivo debe ser Excel (.xlsx o .xls).')
                return render(request, 'materias/importar_materias.html', {
                    'periodo_seleccionado': periodo_seleccionado,
                })

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
                'periodo_seleccionado': periodo_seleccionado,
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
                'periodo_seleccionado': periodo_seleccionado,
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
            errores = []

            for fila in preview_data:
                try:
                    materia_existente = Materia.objects.filter(
                        periodo=periodo_seleccionado,
                        clave=fila['clave']
                    ).first()

                    if materia_existente:
                        materia_existente.nombre = fila['nombre']
                        materia_existente.semestre = int(fila['semestre'])
                        materia_existente.full_clean()
                        materia_existente.save()
                        actualizadas += 1
                    else:
                        materia = Materia(
                            periodo=periodo_seleccionado,
                            clave=fila['clave'],
                            nombre=fila['nombre'],
                            semestre=int(fila['semestre']),
                            es_especialidad=False,
                        )
                        materia.full_clean()
                        materia.save()
                        creadas += 1

                except ValidationError as e:
                    errores.append(f"{fila['clave']}: {e}")
                except Exception as e:
                    errores.append(f"{fila['clave']}: {str(e)}")

            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

            if errores:
                messages.warning(
                    request,
                    f'Importación parcial. Creadas: {creadas}. Actualizadas: {actualizadas}. Errores: {len(errores)}.'
                )
            else:
                messages.success(
                    request,
                    f'Importación completada. Materias creadas: {creadas}. Materias actualizadas: {actualizadas}.'
                )

            return redirect('core:lista_materias')

    return render(request, 'materias/importar_materias.html', {
        'periodo_seleccionado': periodo_seleccionado,
    })


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

            password_temporal = Usuario.objects.make_random_password()

            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password_temporal,
                first_name=first_name,
                last_name=last_name,
                rol=Usuario.DOCENTE,
            )
            Usuario.objects.filter(pk=usuario.pk).update(
                password_temporal=password_temporal
            )

            messages.success(request, f"Docente '{usuario.username}' creado correctamente.")
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
                # Guardar la nueva contraseña para que el admin pueda verla
                usuario.password_temporal = nueva_pass
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


# =========================
# CURSOS Y PERIODOS
# =========================

@login_required
@solo_admin
def lista_cursos(request):
    periodo_id = request.session.get('periodo_seleccionado_id')
    periodo_seleccionado = Periodo.objects.filter(pk=periodo_id).first()

    if not periodo_seleccionado:
        periodo_seleccionado = Periodo.objects.filter(es_activo=True).first()

    cursos = Curso.objects.none()
    if periodo_seleccionado:
        cursos = Curso.objects.filter(
            materia__periodo=periodo_seleccionado
        ).select_related(
            'materia',
            'materia__periodo',
            'docente'
        ).order_by(
            'materia__semestre',
            'materia__clave',
            'grupo'
        )

    return render(request, 'cursos/lista_cursos.html', {
        'cursos': cursos,
        'periodo_activo': periodo_seleccionado,
    })


@login_required
@solo_admin
def crear_curso(request):
    periodo_id = request.session.get('periodo_seleccionado_id')
    periodo_seleccionado = Periodo.objects.filter(pk=periodo_id).first()

    if not periodo_seleccionado:
        periodo_seleccionado = Periodo.objects.filter(es_activo=True).first()

    if not periodo_seleccionado:
        messages.error(request, 'No hay ningún periodo seleccionado o activo para crear cursos.')
        return redirect('core:lista_periodos')

    if request.method == 'POST':
        form = CursoForm(request.POST, periodo=periodo_seleccionado)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.full_clean()
            curso.save()
            messages.success(request, 'Curso creado correctamente.')
            return redirect('core:lista_cursos')
    else:
        form = CursoForm(periodo=periodo_seleccionado, initial={'grupo': 'A'})

    return render(request, 'cursos/form_curso.html', {
        'form': form,
        'titulo': 'Crear curso',
        'periodo_activo': periodo_seleccionado,
    })

@login_required
@solo_admin
def editar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    periodo_seleccionado = curso.materia.periodo

    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso, periodo=periodo_seleccionado)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.full_clean()
            curso.save()
            messages.success(request, 'Curso actualizado correctamente.')
            return redirect('core:lista_cursos')
    else:
        form = CursoForm(instance=curso, periodo=periodo_seleccionado)

    return render(request, 'cursos/form_curso.html', {
        'form': form,
        'titulo': 'Editar curso',
        'periodo_activo': periodo_seleccionado,
        'curso': curso,
    })


@login_required
@solo_admin
def eliminar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)

    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado correctamente.')
        return redirect('core:lista_cursos')

    return render(request, 'cursos/confirmar_eliminar.html', {
        'curso': curso,
    })


@login_required
@solo_admin
def crear_periodo(request):
    if request.method == 'POST':
        form = PeriodoForm(request.POST)
        if form.is_valid():
            periodo = form.save(commit=False)
            if periodo.es_activo:
                Periodo.objects.filter(es_activo=True).update(es_activo=False)
            periodo.save()
            messages.success(request, f'Periodo "{periodo.nombre}" creado correctamente.')
            return redirect('core:lista_periodos')
    else:
        form = PeriodoForm()

    return render(request, 'periodos/form_periodo.html', {
        'form': form,
        'titulo': 'Agregar Periodo',
    })


@login_required
@solo_admin
def lista_periodos(request):
    periodos = Periodo.objects.all().order_by('-fecha_inicio')
    return render(request, 'periodos/lista_periodos.html', {
        'periodos': periodos,
    })


@login_required
@solo_admin
def eliminar_periodo(request, pk):
    periodo = get_object_or_404(Periodo, pk=pk)
    cursos_asociados = periodo.cursos.count()

    if request.method == 'POST':
        periodo.cursos.all().delete()
        periodo.delete()
        messages.success(request, f'Periodo "{periodo.nombre}" y sus {cursos_asociados} curso(s) eliminados correctamente.')
        return redirect('core:lista_periodos')

    return render(request, 'periodos/confirmar_eliminar.html', {
        'periodo': periodo,
        'cursos_asociados': cursos_asociados,
    })


@login_required
@solo_admin
def editar_periodo(request, pk):
    periodo = get_object_or_404(Periodo, pk=pk)
    next_action = request.POST.get('next_action', '')

    if request.method == 'POST':
        form = PeriodoForm(request.POST, instance=periodo)
        if form.is_valid():
            periodo = form.save(commit=False)
            if periodo.es_activo:
                Periodo.objects.filter(es_activo=True).exclude(pk=periodo.pk).update(es_activo=False)
            periodo.save()
            messages.success(request, f'Periodo "{periodo.nombre}" actualizado correctamente.')

            if next_action == 'agregar_otro':
                return redirect('core:crear_periodo')
            elif next_action == 'continuar_editando':
                return redirect('core:editar_periodo', pk=periodo.pk)
            else:
                return redirect('core:lista_periodos')
    else:
        form = PeriodoForm(instance=periodo)

    return render(request, 'periodos/form_periodo.html', {
        'form': form,
        'titulo': 'Editar Periodo',
        'periodo': periodo,
    })


@solo_admin
def importar_docentes(request):
    hojas = []
    archivo_temporal = None
    hoja_seleccionada = None
    preview_data = []
    resumen_creados = []

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # PASO 1: subir archivo
        if accion == 'subir_archivo':
            archivo = request.FILES.get('archivo_excel')

            if not archivo:
                messages.error(request, 'Debes seleccionar un archivo Excel.')
                return render(request, 'usuarios/importar_docentes.html')

            if not archivo.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'El archivo debe ser Excel (.xlsx o .xls).')
                return render(request, 'usuarios/importar_docentes.html')

            carpeta_temp = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
            os.makedirs(carpeta_temp, exist_ok=True)

            fs = FileSystemStorage(location=carpeta_temp)
            nombre_archivo = fs.save(archivo.name, archivo)
            archivo_temporal = nombre_archivo
            ruta_archivo = fs.path(nombre_archivo)

            try:
                hojas = obtener_hojas_excel_docentes(ruta_archivo)
                messages.success(request, 'Archivo cargado correctamente. Ahora selecciona una hoja.')
            except ImportadorDocentesError as e:
                fs.delete(nombre_archivo)
                messages.error(request, str(e))

            return render(request, 'usuarios/importar_docentes.html', {
                'hojas': hojas,
                'archivo_temporal': archivo_temporal,
            })

        # PASO 2: analizar hoja
        elif accion == 'analizar_hoja':
            hoja_seleccionada = request.POST.get('hoja')
            archivo_temporal = request.POST.get('archivo_temporal')

            if not hoja_seleccionada or not archivo_temporal:
                messages.error(request, 'Debes seleccionar una hoja válida.')
                return redirect('core:importar_docentes')

            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'temp_imports', archivo_temporal)

            try:
                hojas = obtener_hojas_excel_docentes(ruta_archivo)
                preview_data = analizar_hoja_docentes(ruta_archivo, hoja_seleccionada)

                for fila in preview_data:
                    existe = Usuario.objects.filter(
                        rol=Usuario.DOCENTE,
                        first_name__iexact=fila['first_name'],
                        last_name__iexact=fila['last_name'],
                    ).exists()
                    fila['estado'] = 'Ya existe' if existe else 'Nuevo'

                messages.success(request, f'Se detectaron {len(preview_data)} docentes únicos.')
            except ImportadorDocentesError as e:
                messages.error(request, str(e))

            return render(request, 'usuarios/importar_docentes.html', {
                'hojas': hojas,
                'archivo_temporal': archivo_temporal,
                'hoja_seleccionada': hoja_seleccionada,
                'preview_data': preview_data,
            })

        # PASO 3: guardar docentes
        elif accion == 'guardar_docentes':
            hoja_seleccionada = request.POST.get('hoja')
            archivo_temporal = request.POST.get('archivo_temporal')

            if not hoja_seleccionada or not archivo_temporal:
                messages.error(request, 'No se pudo recuperar la información para guardar.')
                return redirect('core:importar_docentes')

            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'temp_imports', archivo_temporal)

            if not os.path.exists(ruta_archivo):
                messages.error(request, 'El archivo temporal ya no existe. Vuelve a cargar el Excel.')
                return redirect('core:importar_docentes')

            try:
                preview_data = analizar_hoja_docentes(ruta_archivo, hoja_seleccionada)
            except ImportadorDocentesError as e:
                messages.error(request, str(e))
                return redirect('core:importar_docentes')

            creados = 0
            omitidos = 0
            resumen_creados = []

            for fila in preview_data:
                existe = Usuario.objects.filter(
                    rol=Usuario.DOCENTE,
                    first_name__iexact=fila['first_name'],
                    last_name__iexact=fila['last_name'],
                ).first()

                if existe:
                    omitidos += 1
                    continue

                username_base = fila['username_base']
                username_final = username_base
                contador = 1

                while Usuario.objects.filter(username=username_final).exists():
                    username_final = f"{username_base}{contador}"
                    contador += 1

                password_temporal = Usuario.objects.make_random_password()

                usuario = Usuario.objects.create_user(
                    username=username_final,
                    first_name=fila['first_name'],
                    last_name=fila['last_name'],
                    email='',
                    password=password_temporal,
                    rol=Usuario.DOCENTE,
                )
                usuario.password_temporal = password_temporal
                usuario.save(update_fields=['password_temporal'])

                creados += 1
                resumen_creados.append({
                    'nombre': usuario.get_full_name() or usuario.username,
                    'username': usuario.username,
                    'password_temporal': password_temporal,
                })

    return render(request, 'usuarios/importar_docentes.html')


@solo_admin
def importar_cursos(request):
    hojas = []
    archivo_temporal = None
    hoja_seleccionada = None
    preview_data = []
    periodo_detectado = None

    periodo_activo_bd = Periodo.objects.filter(es_activo=True).first()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # PASO 1: subir archivo
        if accion == 'subir_archivo':
            archivo = request.FILES.get('archivo_excel')

            if not archivo:
                messages.error(request, 'Debes seleccionar un archivo Excel.')
                return render(request, 'cursos/importar_cursos.html', {
                    'periodo_activo': periodo_activo_bd,
                })

            if not archivo.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'El archivo debe ser Excel (.xlsx o .xls).')
                return render(request, 'cursos/importar_cursos.html', {
                    'periodo_activo': periodo_activo_bd,
                })

            carpeta_temp = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
            os.makedirs(carpeta_temp, exist_ok=True)

            fs = FileSystemStorage(location=carpeta_temp)
            nombre_archivo = fs.save(archivo.name, archivo)
            archivo_temporal = nombre_archivo
            ruta_archivo = fs.path(nombre_archivo)

            try:
                hojas = obtener_hojas_excel_cursos(ruta_archivo)
                messages.success(request, 'Archivo cargado correctamente. Ahora selecciona una hoja.')
            except ImportadorCursosError as e:
                fs.delete(nombre_archivo)
                messages.error(request, str(e))

            return render(request, 'cursos/importar_cursos.html', {
                'hojas': hojas,
                'archivo_temporal': archivo_temporal,
                'periodo_activo': periodo_activo_bd,
            })

        # PASO 2: analizar hoja
        elif accion == 'analizar_hoja':
            hoja_seleccionada = request.POST.get('hoja')
            archivo_temporal = request.POST.get('archivo_temporal')

            if not hoja_seleccionada or not archivo_temporal:
                messages.error(request, 'Debes seleccionar una hoja válida.')
                return redirect('core:importar_cursos')

            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'temp_imports', archivo_temporal)

            # Detectar periodo desde el Excel
            periodo_detectado = parsear_periodo_desde_excel(ruta_archivo, hoja_seleccionada)

            if periodo_detectado:
                codigo = periodo_detectado['codigo']
                periodo_en_bd = Periodo.objects.filter(codigo=codigo).first()

                if periodo_en_bd:
                    periodo_para_analisis = periodo_en_bd
                else:
                    periodo_para_analisis = Periodo(
                        codigo=codigo,
                        nombre=periodo_detectado['nombre'],
                        fecha_inicio=periodo_detectado['fecha_inicio'],
                        fecha_fin=periodo_detectado['fecha_fin'],
                        es_activo=False,
                    )
            elif periodo_activo_bd:
                periodo_para_analisis = periodo_activo_bd
            else:
                messages.error(request, 'No se pudo detectar el periodo desde el Excel y no hay periodo activo.')
                return render(request, 'cursos/importar_cursos.html', {
                    'hojas': hojas,
                    'archivo_temporal': archivo_temporal,
                })

            materias_periodo = Materia.objects.filter(periodo=periodo_para_analisis)
            docentes = Usuario.objects.filter(rol=Usuario.DOCENTE)
            cursos_periodo = Curso.objects.filter(materia__periodo=periodo_para_analisis)

            try:
                hojas = obtener_hojas_excel_cursos(ruta_archivo)
                preview_data = analizar_hoja_cursos(
                    ruta_archivo,
                    hoja_seleccionada,
                    periodo_para_analisis,
                    materias_periodo,
                    docentes,
                    cursos_periodo,
                )

                resumen = {
                    'total': len(preview_data),
                    'listo_para_crear': sum(1 for fila in preview_data if fila['estado'] == 'Listo para crear'),
                    'listo_para_actualizar': sum(1 for fila in preview_data if fila['estado'] == 'Listo para actualizar'),
                    'curso_ya_existe': sum(1 for fila in preview_data if fila['estado'] == 'Curso ya existe'),
                    'docente_no_encontrado': sum(1 for fila in preview_data if fila['estado'] == 'Docente no encontrado'),
                    'materia_no_encontrada': sum(1 for fila in preview_data if fila['estado'] == 'Materia no encontrada'),
                    'no_corresponde_periodo': sum(1 for fila in preview_data if fila['estado'] == 'No corresponde al periodo'),
                    'semestre_invalido': sum(1 for fila in preview_data if fila['estado'] == 'Semestre inválido'),
                }

                preview_data_filtrada = [
                    fila for fila in preview_data
                    if fila['estado'] in [
                        'Listo para crear',
                        'Listo para actualizar',
                        'Curso ya existe',
                        'Docente no encontrado',
                        'Materia no encontrada',
                    ]
                ]

                messages.success(request, f"Se analizaron {resumen['total']} filas.")

            except ImportadorCursosError as e:
                messages.error(request, str(e))
                preview_data_filtrada = []
                resumen = {}

            return render(request, 'cursos/importar_cursos.html', {
                'hojas': hojas,
                'archivo_temporal': archivo_temporal,
                'hoja_seleccionada': hoja_seleccionada,
                'preview_data': preview_data_filtrada,
                'periodo_activo': periodo_para_analisis,
                'periodo_detectado': periodo_detectado,
                'resumen': resumen,
            })

        # PASO 3: guardar cursos
        elif accion == 'guardar_cursos':
            hoja_seleccionada = request.POST.get('hoja')
            archivo_temporal = request.POST.get('archivo_temporal')

            if not hoja_seleccionada or not archivo_temporal:
                messages.error(request, 'No se pudo recuperar la información para guardar.')
                return redirect('core:importar_cursos')

            ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'temp_imports', archivo_temporal)

            if not os.path.exists(ruta_archivo):
                messages.error(request, 'El archivo temporal ya no existe. Vuelve a cargar el Excel.')
                return redirect('core:importar_cursos')

            periodo_detectado = parsear_periodo_desde_excel(ruta_archivo, hoja_seleccionada)

            if periodo_detectado:
                codigo = periodo_detectado['codigo']
                periodo_existente = Periodo.objects.filter(codigo=codigo).first()

                if periodo_existente:
                    periodo_para_guardar = periodo_existente
                else:
                    periodo_mas_reciente = Periodo.objects.order_by('-fecha_inicio').first()
                    es_el_mas_reciente = (
                        not periodo_mas_reciente or
                        periodo_detectado['fecha_inicio'] >= periodo_mas_reciente.fecha_inicio
                    )

                    if es_el_mas_reciente:
                        Periodo.objects.filter(es_activo=True).update(es_activo=False)

                    periodo_para_guardar = Periodo.objects.create(
                        codigo=codigo,
                        nombre=periodo_detectado['nombre'],
                        fecha_inicio=periodo_detectado['fecha_inicio'],
                        fecha_fin=periodo_detectado['fecha_fin'],
                        es_activo=es_el_mas_reciente,
                    )
                    messages.success(request, f'Periodo "{periodo_para_guardar.nombre}" creado automáticamente.')
            elif periodo_activo_bd:
                periodo_para_guardar = periodo_activo_bd
            else:
                messages.error(request, 'No se pudo detectar ni encontrar un periodo para importar los cursos.')
                return redirect('core:importar_cursos')

            materias_periodo = Materia.objects.filter(periodo=periodo_para_guardar)
            docentes = Usuario.objects.filter(rol=Usuario.DOCENTE)
            cursos_periodo = Curso.objects.filter(materia__periodo=periodo_para_guardar)

            try:
                preview_data = analizar_hoja_cursos(
                    ruta_archivo,
                    hoja_seleccionada,
                    periodo_para_guardar,
                    materias_periodo,
                    docentes,
                    cursos_periodo,
                )
            except ImportadorCursosError as e:
                messages.error(request, str(e))
                return redirect('core:importar_cursos')

            creados = 0
            actualizados = 0
            omitidos = 0

            for fila in preview_data:
                if fila['estado'] not in ['Listo para crear', 'Listo para actualizar', 'Curso ya existe']:
                    omitidos += 1
                    continue

                materia = Materia.objects.filter(
                    id=fila['materia_id'],
                    periodo=periodo_para_guardar
                ).first()

                docente = Usuario.objects.filter(
                    id=fila['docente_id'],
                    rol=Usuario.DOCENTE
                ).first()

                if not materia or not docente:
                    omitidos += 1
                    continue

                curso, created = Curso.objects.update_or_create(
                    materia=materia,
                    grupo='A',
                    defaults={
                        'docente': docente,
                    }
                )

                if created:
                    creados += 1
                else:
                    actualizados += 1

            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

            messages.success(
                request,
                f'Importación completada. Cursos creados: {creados}. Cursos actualizados: {actualizados}. Filas omitidas: {omitidos}.'
            )
            return redirect('core:lista_periodos')

    return render(request, 'cursos/importar_cursos.html', {
        'periodo_activo': periodo_activo_bd,
    })