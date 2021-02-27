from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from psct.models import pontuacao as models

admin.site.register(models.FaseAjustePontuacao, CompareVersionAdmin)
