from django import forms
from django.utils import timezone
from .models import LeaveRequest

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {"start_date": forms.DateInput(attrs={"type":"date"}), "end_date": forms.DateInput(attrs={"type":"date"}), "reason": forms.Textarea(attrs={"rows":4})}
    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start: self.add_error("end_date", "End date must be on or after start date.")
        if start and start < timezone.localdate(): self.add_error("start_date", "Start date cannot be in the past.")
        return data
