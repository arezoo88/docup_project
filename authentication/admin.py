import csv
from django.contrib import admin
from django.contrib.auth.models import Group
from django.http import HttpResponse
from authentication.models import Doctor, User, Patient, Clinic,ClinicPlan ,DoctorSupports, WorkDay,WorkTime, SuggestedDoctor,VisitType
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from follow_up.models import Screening
from django.utils.html import format_html

admin.site.unregister(Group)


class WorkTimeInLine(NestedStackedInline):
    model = WorkTime
    extra = 1

class WorkDayInLine(NestedStackedInline):
    model= WorkDay
    extra = 1
    inlines = [
        WorkTimeInLine,
    ]

class VisitTypeInLine(NestedStackedInline):
    model= VisitType
    extra = 1
    inlines = [
        WorkDayInLine,
    ]
class DoctorSupportsTestInLined(NestedModelAdmin):
    model = DoctorSupports
    inlines = [
        VisitTypeInLine,
    ]


admin.site.register(DoctorSupports, DoctorSupportsTestInLined)


class UserAdminS(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'superuser_status', 'avatar_img')
    search_fields = ('username', 'first_name', 'last_name',)

    def avatar_img(self, obj):
        if obj.avatar:
            return format_html('<img src="{0}" style="width: 45px; height:45px;border-radius:50%" />'.format(obj.avatar.url))
        else:
            return '-'

    def superuser_status(self, obj):
        colors = {
            True: 'green',
            False: '',
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors[obj.is_superuser],
            obj.is_superuser,
        )


admin.site.register(User, UserAdminS)


class UserAdminDoctor(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'expert')
    search_fields = ('user__first_name', 'user__last_name', 'expert')

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    class Meta:
        model = Doctor


admin.site.register(Doctor, UserAdminDoctor)


class UserAdminPatient(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name',)
    search_fields = ('user__first_name', 'user__last_name',)

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    class Meta:
        model = Patient


admin.site.register(Patient, UserAdminPatient)

class ClinicPlanInLine(NestedStackedInline):
    model = ClinicPlan
    extra = 1


class ScreeningInLine(NestedStackedInline):
    model = Screening
    extra = 1
    max_num = 1

class UserAdminClinic(NestedModelAdmin):
    model= Clinic
    list_display = ('user', 'first_name', 'last_name',)
    search_fields = ('user__first_name', 'user__last_name',)

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name
    inlines = [
        ScreeningInLine,
        ClinicPlanInLine
    ]
admin.site.register(Clinic,UserAdminClinic)

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


class UserAdminSuggestedDoctor(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('first_name', 'last_name',)
    search_fields = ('first_name',)
    actions = ["export_as_csv"]

    class Meta:
        model = SuggestedDoctor


admin.site.register(SuggestedDoctor, UserAdminSuggestedDoctor)