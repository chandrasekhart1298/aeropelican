from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("employees", "0003_payslip_document")]
    operations = [migrations.AddField(model_name="auditlog", name="employee", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to="employees.employee"))]
