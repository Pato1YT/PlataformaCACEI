from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='password_temporal',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=128,
                help_text='Contraseña temporal visible para el administrador.',
            ),
        ),
    ]