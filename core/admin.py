
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario

    list_display  = ('telefone', 'nome', 'ativo', 'is_staff')
    list_filter   = ('ativo', 'is_staff', 'is_superuser')
    search_fields = ('telefone', 'nome')
    ordering      = ('telefone',)

    fieldsets = (
        (None,           {'fields': ('telefone', 'nome', 'password')}),
        ('Opções Pessoais', {'fields': ('chave_pix', 'ativo')}),
        ('Permissões',   {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telefone', 'nome', 'password1', 'password2'),
        }),
    )