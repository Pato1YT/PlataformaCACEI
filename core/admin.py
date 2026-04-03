from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Usuario,
    AtributoEgreso,
    Materia,
    Evidencia,
    ReporteNivelLogro,
    Periodo
)

# Register your models here.

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_staff')


admin.site.register(AtributoEgreso)
admin.site.register(Materia)
admin.site.register(Evidencia)
admin.site.register(ReporteNivelLogro)
admin.site.register(Periodo)