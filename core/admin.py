from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, AuthenticationForm as DjangoAuthenticationForm
from django import forms # Importa o módulo forms para ValidationError
from .models import Usuario

# 1. Crie um formulário personalizado para ALTERAR um usuário no admin
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        # Defina explicitamente os campos que você quer no formulário de alteração.
        # Certifique-se de incluir 'telefone' e 'nome'.
        # 'password' é manipulado separadamente por UserChangeForm.
        fields = (
            'telefone', 'nome', 'chave_pix', 'ativo',
            'is_active', 'is_staff', 'is_superuser', 
            'groups', 'user_permissions', 'last_login' 
        )

# 2. Crie um formulário personalizado para CRIAR um usuário no admin
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Defina explicitamente os campos que você quer no formulário de criação.
        # 'password' e 'password2' são manipulados automaticamente por UserCreationForm.
        fields = (
            'telefone', 'nome', 'chave_pix', 'ativo',
            'is_active', 'is_staff', 'is_superuser', 
            'groups', 'user_permissions'
        )

    # Opcional: Adicione validação para garantir que o telefone seja único ao criar
    # (Embora o campo `unique=True` no modelo já faça isso no banco,
    # essa validação em formulário oferece feedback mais rápido)
    def clean_telefone(self):
        telefone = self.cleaned_data['telefone']
        if self.instance.pk is None and Usuario.objects.filter(telefone=telefone).exists():
            raise forms.ValidationError("Um usuário com este telefone já existe.")
        return telefone

# 3. Crie um formulário de autenticação personalizado para o Admin
class CustomAdminAuthenticationForm(DjangoAuthenticationForm):
    """
    Formulário de autenticação para o admin que utiliza o 'telefone' como USERNAME_FIELD.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Renomeia o rótulo do campo 'username' para 'telefone'
        if 'username' in self.fields:
            self.fields['username'].label = 'Telefone'

    def clean(self):
        # A lógica de validação padrão de AuthenticationForm é executada aqui.
        # No entanto, ao usar um USERNAME_FIELD customizado, o campo de entrada
        # 'username' será validado contra o campo 'telefone' do seu modelo.
        # Não precisamos mudar a lógica de clean, apenas o rótulo.
        return super().clean()

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # 4. Associe os formulários personalizados ao seu UserAdmin
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    # Campos exibidos na lista de usuários no admin
    list_display  = ('telefone', 'nome', 'ativo', 'is_staff', 'is_superuser')
    list_filter   = ('ativo', 'is_staff', 'is_superuser')
    search_fields = ('telefone', 'nome')
    ordering      = ('telefone',)

    # fieldsets para o formulário de ALTERAÇÃO de usuário (editar um usuário existente)
    fieldsets = (
        (None,                   {'fields': ('telefone', 'nome', 'password')}),
        ('Opções Pessoais',      {'fields': ('chave_pix', 'ativo')}),
        ('Permissões',           {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes',    {'fields': ('last_login',)}), 
    )
    
    # fieldsets para o formulário de CRIAÇÃO de usuário (adicionar um novo usuário)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telefone', 'nome', 'password', 'password2'),
        }),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Opções Pessoais', {'fields': ('chave_pix', 'ativo')}),
    )

    # Configuração para exibir ManyToMany fields como caixas de seleção multi-seleção
    filter_horizontal = ('groups', 'user_permissions',)

# 5. Sobrescreva o formulário de autenticação padrão do Admin
# Isso é crucial para que o painel de admin use seu campo 'telefone' para login
admin.site.login_form = CustomAdminAuthenticationForm


from django.contrib import admin
from .models import Aposta

def validar_aposta(modeladmin, request, queryset):
    queryset.update(status='valida')


def rejeitar_aposta(modeladmin, request, queyset):
    queyset.update(status='rejeitada')



@admin.register(Aposta)
class ApostaAdmin(admin.ModelAdmin):
    
    list_display = ('usuario', 'data_aposta','sexo_escolha', 'valor_aposta', 'status')

    list_filter = ('status', 'sexo_escolha')

    search_fields = ('usuario__nome', 'status')

    ordering = ('-data_aposta',)

    fieldsets = (
    (None, {'fields': ('usuario', 'sexo_escolha', 'valor_aposta', 'valor_para_pote', 'status')}),
    ('Opções de Status', {'fields': ('ativo', 'is_active', 'is_staff', 'is_superuser')}),
    )

      # Exemplo de como você pode adicionar o relatório em uma página customizada
    def changelist_view(self, request, extra_context=None):
        # Pega o relatório financeiro
        relatorio = Aposta.objects.get_relatorio_financeiro()
        # Adiciona o relatório financeiro ao contexto
        extra_context = extra_context or {}
        extra_context['relatorio_financeiro'] = relatorio

        return super().changelist_view(request, extra_context=extra_context)
    
    actions = [validar_aposta, rejeitar_aposta]

    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle any custom saving logic.
        This can be used to log changes or perform other actions before saving.
        """
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Customize the queryset for filtering or limiting the records shown.
        """
        queryset = super().get_queryset(request)

        if not request.user.is_staff:
            queryset = queryset.filter(usuario=request.user)
        return queryset
    

