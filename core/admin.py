from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Usuario,
    AtributoEgreso,
    Materia,
    Periodo,
    Curso,
    CriterioDesempeno,
    Indicador,
    EvidenciaIndicador,
    ResultadoIndicador
    
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
admin.site.register(Periodo)
admin.site.register(Curso)
admin.site.register(CriterioDesempeno)
admin.site.register(Indicador)
admin.site.register(EvidenciaIndicador)
admin.site.register(ResultadoIndicador)