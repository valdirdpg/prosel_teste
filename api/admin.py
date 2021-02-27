from rest_framework.authtoken.admin import TokenAdmin

from api.forms import TokenForm

TokenAdmin.form = TokenForm
