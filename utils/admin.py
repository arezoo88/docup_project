from utils.models import ImageList, Image,Voucher,City


from django.contrib import admin
from django.contrib.admin.models import LogEntry
#admin file is for display data in admin panel
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code','discount','enabled')
    search_fields = ('code','discount')

admin.site.register(Voucher,VoucherAdmin)

class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id','city_title')
    search_fields = ('city_id','city_title')

admin.site.register(City,CityAdmin)


class LogEntryAdmin(admin.ModelAdmin):
    # list_display = ("user",)
    readonly_fields = ('content_type',
        'user',
        'action_time',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message'
    )
    search_fields = ("user__username",)
    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(LogEntryAdmin, self).get_actions(request)
        print(actions)
        # del actions['delete_selected']
        return actions

admin.site.register(LogEntry,LogEntryAdmin)


admin.site.register(ImageList)
admin.site.register(Image)
