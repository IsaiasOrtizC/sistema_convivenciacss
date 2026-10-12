from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_casos', '0011_reglainstitucional_disposicion_verificada'),
    ]

    operations = [
        migrations.AddField(
            model_name='reglainstitucional',
            name='tipo_medida',
            field=models.CharField(
                choices=[
                    ('clasificacion', 'Clasificación de falta'),
                    ('pedagogica', 'Medida pedagógica/formativa'),
                    ('reparatoria', 'Medida reparatoria'),
                    ('preventiva', 'Medida preventiva'),
                    ('sancion_disciplinaria', 'Sanción disciplinaria'),
                    ('resolucion_alternativa', 'Resolución alternativa de conflictos'),
                    ('no_clasificada', 'Tipo de medida pendiente de verificar'),
                ],
                default='no_clasificada',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='version_fuente',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
