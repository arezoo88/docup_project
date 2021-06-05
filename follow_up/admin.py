from django.contrib import admin

# Register your models here.
from follow_up.models import Panel, DQAnswer, DiseaseQuestion, Ticket, Visit, ClinicService, HealthEvent, Drug, Article, \
    DynamicPanelImageListField,BankLogo,Notification,VisitPlan,ScreeningSteps,Ica
from nested_inline.admin import NestedStackedInline, NestedModelAdmin

class IcaInLine(NestedStackedInline):
    model = Ica
    extra = 1
    max_num = 1

class ScreeningStepsInline(NestedModelAdmin):
    model= ScreeningSteps
    list_display = ('screening', 'discount','patient_name','doctor_name')
    # search_fields = ('user__first_name', 'user__last_name',)

    def patient_name(self, obj):
        if obj.patient:
            return str(obj.patient.user.first_name) + " " + str(obj.patient.user.last_name)

    def doctor_name(self, obj):
        if obj.panel:
            return str(obj.panel.doctor.user.first_name) + " " + str(obj.panel.doctor.user.last_name)

    inlines = [
        IcaInLine
    ]




admin.site.register(ScreeningSteps,ScreeningStepsInline)

class PanelAdmin(admin.ModelAdmin):
    list_display = ('panel_id', 'doctor_name', 'patient_id', 'patient_name')
    search_fields = ("doctor__user__first_name", 'doctor__user__last_name', 'patient__user__first_name',
                     'patient__user__last_name')

    def doctor_name(self, obj):
        if obj.doctor:
            return str(obj.doctor.user.first_name) + " " + str(obj.doctor.user.last_name)

    def patient_name(self, obj):
        if obj.patient:
            return str(obj.patient.user.first_name)

    def panel_id(self, obj):
        return str(obj.id)

    def patient_id(self, obj):
        if obj.patient:
            return str(obj.patient.id)


admin.site.register(Panel, PanelAdmin)
# admin.site.register(Prescription)
# admin.site.register(DiseaseQuestion)
# admin.site.register(DQAnswer)
admin.site.register(Ticket)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('visit_id', 'doctor_name', 'patient_id', 'patient_name')
    search_fields = ("doctor__user__first_name", 'doctor__user__last_name', 'patient__user__first_name',
                     'patient__user__last_name')

    def doctor_name(self, obj):
        if obj.doctor:
            return str(obj.doctor.user.first_name) + " " + str(obj.doctor.user.last_name)

    def patient_name(self, obj):
        if obj.patient:
            return str(obj.patient.user.first_name)

    def visit_id(self, obj):
        return str(obj.id)

    def patient_id(self, obj):
        if obj.patient:
            return str(obj.patient.id)
class VisitPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_id', 'doctor_name', 'patient_id', 'patient_name')
    search_fields = ("doctor__user__first_name", 'doctor__user__last_name', 'patient__user__first_name',
                     'patient__user__last_name')

    def doctor_name(self, obj):
        if obj.doctor:
            return str(obj.doctor.user.first_name) + " " + str(obj.doctor.user.last_name)

    def patient_name(self, obj):
        if obj.patient:
            return str(obj.patient.user.first_name)

    def plan_id(self, obj):
        return str(obj.id)

    def patient_id(self, obj):
        if obj.patient:
            return str(obj.patient.id)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id','owner', 'title','type', 'time', 'is_read')
admin.site.register(Visit,VisitAdmin)
admin.site.register(VisitPlan,VisitPlanAdmin)
admin.site.register(ClinicService)
admin.site.register(HealthEvent)
admin.site.register(Drug)
admin.site.register(Article)
admin.site.register(DynamicPanelImageListField)
admin.site.register(BankLogo)
admin.site.register(Notification,NotificationAdmin)
