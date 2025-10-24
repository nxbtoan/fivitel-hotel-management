from django.contrib import admin
from .models import Ticket, TicketResponse

admin.site.register(Ticket)
admin.site.register(TicketResponse)