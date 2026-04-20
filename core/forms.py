# =============================================================================
# IMPORTS
# =============================================================================

from django import forms
from django.contrib.auth.password_validation import validate_password  # noqa: F401 — disponible para uso futuro

from .models import AtributoEgreso, Curso, Materia, Periodo, Usuario, CriterioDesempeno, Indicador


# =============================================================================
# ATRIBUTOS DE EGRESO
# =============================================================================

class AtributoEgresoForm(forms.ModelForm):
    class Meta:
        model = AtributoEgreso
        fields = ['codigo', 'nombre', 'descripcion']
        widgets = {
            'codigo':      forms.TextInput(attrs={'class': 'form-control'}),
            'nombre':      forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =============================================================================
# MATERIAS
# =============================================================================

class MateriaForm(forms.ModelForm):
    def __init__(self, *args, periodo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.periodo = periodo

    class Meta:
        model = Materia
        fields = ['clave', 'nombre', 'semestre', 'es_especialidad']
        widgets = {
            'clave':          forms.TextInput(attrs={'class': 'form-control'}),
            'nombre':         forms.TextInput(attrs={'class': 'form-control'}),
            'semestre':       forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
            'es_especialidad': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_semestre(self):
        semestre = self.cleaned_data.get('semestre')
        if semestre is None:
            raise forms.ValidationError('El semestre es obligatorio.')
        if semestre < 1 or semestre > 8:
            raise forms.ValidationError('El semestre debe ser un valor entre 1 y 8.')

        if self.periodo:
            if self.periodo.tipo_oferta == Periodo.PAR and semestre % 2 != 0:
                raise forms.ValidationError('Para un periodo par, el semestre debe ser par.')
            if self.periodo.tipo_oferta == Periodo.IMPAR and semestre % 2 == 0:
                raise forms.ValidationError('Para un periodo impar, el semestre debe ser impar.')

        return semestre


# =============================================================================
# USUARIOS / DOCENTES
# =============================================================================

class CrearDocenteForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username':   'Usuario',
            'first_name': 'Nombre(s)',
            'last_name':  'Apellidos',
            'email':      'Correo electrónico',
        }
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
        }


class EditarPerfilForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email':    forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data


# =============================================================================
# CURSOS
# =============================================================================

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['materia', 'docente', 'grupo']
        labels = {
            'materia': 'Materia',
            'docente': 'Docente',
            'grupo':   'Grupo',
        }
        widgets = {
            'materia': forms.Select(attrs={'class': 'form-control'}),
            'docente': forms.Select(attrs={'class': 'form-control'}),
            'grupo':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. A'}),
        }

    def __init__(self, *args, periodo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.periodo = periodo

        if periodo:
            self.fields['materia'].queryset = Materia.objects.filter(
                periodo=periodo
            ).order_by('semestre', 'clave')
        else:
            self.fields['materia'].queryset = Materia.objects.none()

        self.fields['docente'].queryset = Usuario.objects.filter(
            rol=Usuario.DOCENTE
        ).order_by('first_name', 'last_name', 'username')

    def clean_grupo(self):
        grupo = self.cleaned_data['grupo'].strip().upper()
        return grupo


# =============================================================================
# PERIODOS
# =============================================================================

class PeriodoForm(forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ['codigo', 'nombre', 'fecha_inicio', 'fecha_fin', 'tipo_oferta', 'es_activo']
        labels = {
            'codigo':      'Codigo',
            'nombre':      'Nombre',
            'fecha_inicio': 'Fecha inicio',
            'fecha_fin':   'Fecha fin',
            'tipo_oferta': 'Tipo oferta',
            'es_activo':   'Es activo',
        }
        widgets = {
            'codigo':      forms.TextInput(attrs={'class': 'form-control'}),
            'nombre':      forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'fecha_fin':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'tipo_oferta': forms.Select(attrs={'class': 'form-control'}),
            'es_activo':   forms.CheckboxInput(),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if not codigo.isalnum():
            raise forms.ValidationError('El código solo puede contener letras y números, sin espacios ni caracteres especiales.')
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre.replace(' ', '').replace('-', '').isalnum():
            raise forms.ValidationError('El nombre solo puede contener letras, números, espacios y guiones.')
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin    = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError('La fecha de inicio no puede ser mayor que la fecha de fin.')

        es_activo = cleaned_data.get('es_activo')
        if es_activo:
            # Validar que solo haya un periodo activo
            qs = Periodo.objects.filter(es_activo=True)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Ya existe un periodo activo. Desactívalo antes de activar otro.')

            # Validar que sea el periodo más reciente
            periodo_mas_reciente = Periodo.objects.order_by('-fecha_inicio').first()
            if periodo_mas_reciente and self.instance and self.instance.pk:
                if periodo_mas_reciente.pk != self.instance.pk:
                    raise forms.ValidationError('Solo se puede activar el periodo más reciente.')

        return cleaned_data


# =============================================================================
# CRITERIOS DE DESEMPENO
# =============================================================================

class CriterioDesempenoForm(forms.ModelForm):
    class Meta:
        model = CriterioDesempeno
        fields = ['codigo', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. CD1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# =============================================================================
# INDIDCADORES
# =============================================================================

class IndicadorForm(forms.ModelForm):
    class Meta:
        model = Indicador
        fields = ['codigo', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. I1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }