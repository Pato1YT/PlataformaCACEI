from django import forms
from .models import AtributoEgreso, Materia, Usuario


class AtributoEgresoForm(forms.ModelForm):
    class Meta:
        model = AtributoEgreso
        fields = ['codigo', 'nombre', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['clave', 'nombre', 'semestre', 'es_especialidad']
        widgets = {
            'clave': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'semestre': forms.NumberInput(attrs={'class': 'form-control'}),
            'es_especialidad': forms.CheckboxInput(attrs={'class': 'form-control'}),
            #'nivel': forms.NumberInput(attrs={'class': 'form-control'}),
            #'grupo': forms.TextInput(attrs={'class': 'form-control'}),
            #'periodo': forms.TextInput(attrs={'class': 'form-control'}),
            #'atributo_egreso': forms.Select(attrs={'class': 'form-control'}),
            #'docente': forms.Select(attrs={'class': 'form-control'}),
        }


class CrearDocenteForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre(s)',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
        }