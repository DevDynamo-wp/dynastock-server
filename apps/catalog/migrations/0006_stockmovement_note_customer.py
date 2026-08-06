import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_sale_saleline_stockmovement'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockmovement',
            name='note',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements', to='catalog.customer'),
        ),
        migrations.AlterField(
            model_name='stockmovement',
            name='movement_type',
            field=models.CharField(choices=[('SALE', 'Vente'), ('RESTOCK', 'Réapprovisionnement'), ('ADJUSTMENT', 'Ajustement'), ('INVENTORY', "Comptage d'inventaire"), ('TRANSFER', 'Transfert')], max_length=20),
        ),
    ]