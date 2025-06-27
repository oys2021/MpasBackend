from django.contrib import admin
from core.models import *
# Register your models here.

admin.site.register(PaymentHistory)
admin.site.register(Transaction)
admin.site.register(FeeStructure)
admin.site.register(ProgramFee)

