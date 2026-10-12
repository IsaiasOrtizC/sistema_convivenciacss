from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_casos', '0010_notificacion_evento_tipo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reglainstitucional',
            name='conducta_condicion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='unidad_umbral',
            field=models.CharField(
                blank=True,
                choices=[
                    ('anotaciones', 'Anotaciones'),
                    ('faltas', 'Faltas'),
                    ('reincidencias', 'Reincidencias'),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='cantidad_minima',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='estado_cantidad',
            field=models.CharField(
                choices=[
                    ('definida', 'Cantidad definida en el reglamento'),
                    ('no_especificada', 'El reglamento no especifica cantidad'),
                    ('no_aplica', 'No aplica'),
                    ('no_verificada', 'Cantidad aún no verificada'),
                ],
                default='no_verificada',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='medida_asociada',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='duracion_minima_dias',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='duracion_maxima_dias',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='unidad_duracion',
            field=models.CharField(
                choices=[
                    ('dias', 'Días'),
                    ('dias_habiles', 'Días hábiles'),
                    ('no_verificada', 'Unidad no verificada'),
                ],
                default='no_verificada',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='condiciones',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='excepciones',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='solo_presentacion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='titulo_fuente',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='seccion_fuente',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='pagina_impresa',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='pagina_pdf',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='pagina_impresa_hasta',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reglainstitucional',
            name='pagina_pdf_hasta',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
