from django.contrib import admin
from .models import RoomType, RoomClass, Room, Booking, PaymentProof

class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_class', 'status')

    list_filter = ('status', 'room_class__room_type', 'room_class')

    search_fields = ('room_number',)



admin.site.register(RoomType)
admin.site.register(RoomClass)
admin.site.register(Room, RoomAdmin)
admin.site.register(Booking)
admin.site.register(PaymentProof) 