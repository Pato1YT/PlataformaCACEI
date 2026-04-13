from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
# Create your models here.

# =========================
# USUARIOS DEL SISTEMA
# =========================

class Usuario(AbstractUser):

    ADMINISTRADOR = "ADMINISTRADOR"
    DOCENTE = "DOCENTE"
    VISITANTE = "VISITANTE"

    ROLES = [
        (ADMINISTRADOR, "Administrador / Jefe de carrera"),
        (DOCENTE, "Docente"),
        (VISITANTE, "Visitante"),
    ]

    rol = models.CharField(max_length=20, choices=ROLES, default=VISITANTE)
    password_temporal = models.CharField(max_length=128, blank=True, null=True, help_text="Contraseña temporal visible para el administrador.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"


# =========================
# ATRIBUTOS DE EGRESO
# =========================

class AtributoEgreso(models.Model):
    codigo = models.CharField(max_length=3, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atributo de egreso"
        verbose_name_plural = "Atributos de egreso"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    
# PARA LOS PERIODOS
class Periodo(models.Model):
    PAR = "PAR"
    IMPAR = "IMPAR"

    TIPOS_OFERTA = [
        (PAR, "Semestres pares (2, 4, 6, 8)"),
        (IMPAR, "Semestres impares (1, 3, 5, 7)"),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo_oferta = models.CharField(max_length=10, choices=TIPOS_OFERTA, default=PAR)
    es_activo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")

        if self.es_activo:
            existe_otro_activo = Periodo.objects.filter(es_activo=True).exclude(pk=self.pk).exists()
            if existe_otro_activo:
                raise ValidationError("Solo puede existir un periodo activo a la vez.")
    
    
# =========================
# MATERIAS (RETÍCULA ACADÉMICA)
# =========================

class Materia(models.Model):
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.CASCADE,
        related_name='materias'
    )
    
    atributos_egreso = models.ManyToManyField(
        AtributoEgreso,
        through='MateriaAtributoEgreso',
        related_name='materias',
        blank=True,
    )
    
    clave = models.CharField(max_length=20)
    nombre = models.CharField(max_length=255)
    semestre = models.PositiveIntegerField()
    es_especialidad = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('periodo', 'clave')
        ordering = ['periodo', 'semestre', 'clave']
        
    def __str__(self):
        return f"{self.clave} - {self.nombre} ({self.periodo.codigo})"
    
    def clean(self):
        if not self.periodo_id or not self.semestre:
            return

        if self.periodo.tipo_oferta == Periodo.PAR and self.semestre % 2 != 0:
            raise ValidationError("En un periodo de oferta PAR solo se permiten materias de semestres pares.")

        if self.periodo.tipo_oferta == Periodo.IMPAR and self.semestre % 2 == 0:
            raise ValidationError("En un periodo de oferta IMPAR solo se permiten materias de semestres impares.")
    
# PARA EL CURSO
class Curso(models.Model):
    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name='cursos',
    )
    
    docente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='cursos',
        limit_choices_to={'rol': Usuario.DOCENTE},
    )

    grupo = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        unique_together = ('materia', 'grupo')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.materia.clave} - {self.grupo} ({self.materia.periodo.codigo})"
    
    def clean(self):
        if self.docente and self.docente.rol != Usuario.DOCENTE:
            raise ValidationError("El usuario asignado al curso debe tener rol DOCENTE.")
    
# PARA LOS CRITERIOS E INDICADORES
class CriterioDesempeno(models.Model):
    atributo_egreso = models.ForeignKey(
        AtributoEgreso,
        on_delete=models.PROTECT,
        related_name='criterios',
    )
    
    codigo = models.CharField(max_length=20)
    descripcion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Criterio de desempeño"
        verbose_name_plural = "Criterios de desempeño"
        unique_together = ('atributo_egreso', 'codigo')

    def __str__(self):
        return f"{self.codigo} - {self.descripcion[:40]}..."


class Indicador(models.Model):
    criterio = models.ForeignKey(
        CriterioDesempeno,
        on_delete=models.PROTECT,
        related_name='indicadores',
    )
    
    codigo = models.CharField(max_length=20)
    descripcion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Indicador"
        verbose_name_plural = "Indicadores"
        unique_together = ('criterio', 'codigo')

    def __str__(self):
        return f"{self.codigo} - {self.descripcion[:40]}..."

# PARA RESULTADOS DEL INDICADOR
class ResultadoIndicador(models.Model):
    NIVEL_LOGRO = [
        ('I', 'Inicial'),
        ('M', 'Medio'),
        ('A', 'Avanzado'),
    ]

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='resultados_indicadores',
    )
    indicador = models.ForeignKey(
        Indicador,
        on_delete=models.PROTECT,
        related_name='resultados',
    )
    nivel = models.CharField(max_length=1, choices=NIVEL_LOGRO)
    comentario = models.TextField(blank=True)
    fecha_evaluacion = models.DateTimeField()
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='evaluaciones_registradas',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resultado de indicador"
        verbose_name_plural = "Resultados de indicadores"
        unique_together = ('curso', 'indicador')

    def __str__(self):
        return f"{self.curso} - {self.indicador.codigo} ({self.get_nivel_display()})"
    
    def clean(self):
        if self.usuario and self.usuario.rol not in [Usuario.DOCENTE, Usuario.ADMINISTRADOR]:
            raise ValidationError("Solo un docente o un administrador pueden registrar resultados de indicadores.")

        if self.usuario and self.curso:
            if self.usuario.rol == Usuario.DOCENTE and self.curso.docente_id != self.usuario.id:
                raise ValidationError("El docente que registra el resultado debe ser el docente asignado al curso.")

        if self.curso and self.indicador:
            atributo_indicador = self.indicador.criterio.atributo_egreso

            existe_relacion = MateriaAtributoEgreso.objects.filter(
                materia=self.curso.materia,
                atributo_egreso=atributo_indicador
            ).exists()

            if not existe_relacion:
                raise ValidationError(
                    "El indicador seleccionado no corresponde a un atributo de egreso ligado a la materia del curso."
                )
    
        
class MateriaAtributoEgreso(models.Model):
    NIVEL_APORTE = [
        ('I', 'Inicial'),
        ('M', 'Medio'),
        ('A', 'Avanzado'),
    ]

    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    atributo_egreso = models.ForeignKey(AtributoEgreso, on_delete=models.CASCADE)
    nivel_aporte = models.CharField(max_length=1, choices=NIVEL_APORTE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('materia', 'atributo_egreso')
        verbose_name = "Relación Materia–Atributo"
        verbose_name_plural = "Relaciones Materia–Atributo"

    def __str__(self):
        return f"{self.materia.clave} ↔ {self.atributo_egreso.codigo} ({self.get_nivel_aporte_display()})"


# =========================
# EVIDENCIAS
# =========================

def ruta_evidencia(instance, filename):
    return f"evidencias/curso_{instance.curso.id}/{filename}"


class Evidencia(models.Model):
    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name="evidencias"
    )

    titulo = models.CharField(max_length=255)
    archivo = models.FileField(upload_to=ruta_evidencia)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evidencia"
        verbose_name_plural = "Evidencias"

    def __str__(self):
        return self.titulo


# =========================
# REPORTE DE NIVEL DE LOGRO
# =========================

class ReporteNivelLogro(models.Model):
    materia_atributo = models.OneToOneField(
        MateriaAtributoEgreso,
        on_delete=models.CASCADE,
        related_name="reporte_nivel_logro"
    )
    porcentaje_meta = models.DecimalField(max_digits=5, decimal_places=2)
    porcentaje_obtenido = models.DecimalField(max_digits=5, decimal_places=2)
    comentarios = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reporte de nivel de logro"
        verbose_name_plural = "Reportes de nivel de logro"

    def __str__(self):
        return f"Reporte - {self.materia_atributo.materia.clave} - {self.materia_atributo.atributo_egreso.codigo}"