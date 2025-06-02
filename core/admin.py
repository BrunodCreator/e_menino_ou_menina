from django.contrib import admin
from django import forms
from .models import Usuario

class UsuarioAdminForm(forms.ModelForm):
    """ 
    Formulário usado no Admin para exibir um campo de senha em texto puro(senha_raw),
    e, ao salvar, chamar set_senha() para gerar o hash antes de gravar
    """
    senha_raw = forms.CharField(
        label='Senha (texto puro)',
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text=("Digite sua senha em texto puro"
                  "se não preencher, a senha atual será mantida."
        )
    )
    
    
    class Meta:
        #Devemos omitir o campo 'senha' (hash) da lista de fields
        # Incluir todos os outros campos que o Admin deve exibir
        fields = ('telefone', 'nome', 'chave_pix', 'ativo')
    
    def clean(self):
        """ 
        Validação extra:
        - Se estivermos criando um novo usuário (instance.pk is None), então 'senha_raw' é obrigatório
        - Se for edição (instance.pk existe) e senha_raw vier em branco, mantemos o hash atual.
        """
        cleaned_data = super().clean()
        senha_raw = cleaned_data.get('senha_raw')
        
        #Se for criação de novo usuário e não digitou senha_raw, dá erro:
        if self.instance.pk is None and not senha_raw:
            self.add_error('senha_raw', 'É obrigatório definir uma senha ao criar um novo usuário')
        return cleaned_data

    def save(self, commit=True):
        """
        Ao salvar o ModelForm:
        1) Obtém o objeto Usuario sem gravá-lo ainda (commit=False)
        2) Se senha_raw estiver preenchido, chama set_senha()
        3) Se for edição e senha_raw estiver vazia, mantém o hash anterior
        4) Por fim, chama usuario.save() 
        """
        usuario = super().save(commit=False)
        senha_raw = self.cleaned_data.get('senha_raw')

        if senha_raw:
            usuario.set_senha(senha_raw)
        # Se senha_raw estiver vazio em uma edição, não tocamos no campo 'senha' (hash antigo persiste)

        if commit:
            usuario.save()
        return usuario
        
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    form = UsuarioAdminForm # Aqui indicamos ao Admin para usar o formulário customizado
    
    list_display = ('nome', 'telefone', 'chave_pix')
    list_filter = ('ativo',)
    search_fields = ('nome', 'telefone')

