from django.db import models
from django.contrib.auth.models import AbstractUser
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


# =========================
# MATERIAS (RETÍCULA ACADÉMICA)
# =========================

class Materia(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    
    semestre = models.PositiveIntegerField()
    es_especialidad = models.BooleanField(default=False)
    
    atributos_egreso = models.ManyToManyField(
        AtributoEgreso,
        through="MateriaAtributoEgreso",
        related_name='materias',
        blank=True,
    )

    #docente = models.ForeignKey(
        #Usuario,
        #on_delete=models.PROTECT,
        #related_name="materias",
        #limit_choices_to={'rol': Usuario.DOCENTE}
    #)

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ["semestre", "clave"]

    def __str__(self):
        return f"{self.clave} - {self.nombre}"
    
    
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
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name="reportes"
    )

    porcentaje_meta = models.DecimalField(max_digits=5, decimal_places=2)
    porcentaje_obtenido = models.DecimalField(max_digits=5, decimal_places=2)

    comentarios = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reporte de nivel de logro"
        verbose_name_plural = "Reportes de nivel de logro"

    def __str__(self):
        return f"Reporte - {self.materia}"


# PARA LOS PERIODOS
class Periodo(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    es_activo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    
# PARA EL CURSO
class Curso(models.Model):
    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name='cursos',
    )
    periodo = models.ForeignKey(
        Periodo,
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
        unique_together = ('materia', 'periodo', 'grupo', 'docente')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.materia.clave} - {self.grupo} ({self.periodo.codigo})"
    
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