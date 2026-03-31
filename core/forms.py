from django import forms
from .models import AtributoEgreso, Materia, Usuario
#charco
from django.contrib.auth.password_validation import validate_password


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
        
        #charco
class EditarPerfilForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Nueva contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data
        
