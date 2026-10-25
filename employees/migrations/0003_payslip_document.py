from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("employees", "0002_hrms_modules")]
    operations = [
        migrations.AddField(
            model_name="payslip",
            name="document",
            field=models.FileField(blank=True, null=True, upload_to="payslips/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="payslip",
            name="notes",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
