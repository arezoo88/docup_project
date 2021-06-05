from django.contrib import admin

# Register your models here.
from follow_up.models import Panel2CognitiveTest
from medical_test.models import Question, Answer, CognitiveTest, PatientResponse
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from django.http import HttpResponse
import csv

class AnswerInLine(NestedStackedInline):
    model = Answer
    extra = 1

class QuestionInLine(NestedStackedInline):
    model= Question
    extra = 1
    inlines = [
        AnswerInLine,
    ]

class CognitiveTestInLined(NestedModelAdmin):
    model=CognitiveTest
    inlines = [
        QuestionInLine,
    ]
class Panel2CognitiveTestAdmin(admin.ModelAdmin):
    list_display = ('id','CognitiveTest','panel','done')

admin.site.register(CognitiveTest,CognitiveTestInLined)
admin.site.register(Panel2CognitiveTest,Panel2CognitiveTestAdmin)





class ExportCsvMixin:
    """
        use for csv out put of model in django admin
    """

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([(getattr(obj, field)) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


class PatientResponseAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('patient_name', 'screening_step',)
    search_fields = ('screening_step','patient__user__last_name')
    list_filter = ('screening_step','patient')

    actions = ["export_as_csv"]

    def patient_name(self, obj):
        if obj.patient:
            return str(obj.patient.user.first_name)
    class Meta:
        model = PatientResponse


# admin.site.register(SuggestedDoctor, UserAdminSuggestedDoctor)

admin.site.register(PatientResponse,PatientResponseAdmin)
