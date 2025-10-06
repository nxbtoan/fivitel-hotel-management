from django.contrib import admin
from .models import Ticket, TicketAttachment, TicketResponse

admin.site.register(Ticket)
admin.site.register(TicketAttachment)
admin.site.register(TicketResponse)