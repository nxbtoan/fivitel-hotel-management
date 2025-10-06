from django.contrib import admin
from .models import RoomType, Room, Booking

admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Booking)