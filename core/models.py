from django.db import models

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):
    """
    Modelo para representar os usuários do sistema de apostas do chá de revelação.
    Cada usuário pode fazer login com telefone e nome para participar das apostas.
    """
    
    # ===== VALIDADORES =====
    # Validador customizado para o campo telefone
    telefone_validator = RegexValidator(
        regex=r'^\d{9,11}',  # Aceita 10 ou 11 dígitos numéricos
        message="Telefone deve conter apenas números (9 ou 11 dígitos)"
    )
    
    # ===== CAMPOS DO MODELO =====
    
    telefone = models.CharField(
        verbose_name='Telefone',  # Nome que aparece no admin e formulários
        max_length=11,            # Máximo 11 caracteres (celular com DDD)
        validators=[telefone_validator],  # Aplica a validação de formato
        unique=True,              # Não permite telefones duplicados no banco
        help_text="Digite apenas números, sem espaços ou símbolos (ex: 62999887766)"
    )
    
    nome = models.CharField(
        verbose_name='Nome Completo',
        max_length=100,           # 100 caracteres é suficiente para nomes completos
        help_text="Nome completo do participante"
    )
    
    senha = models.CharField(
        verbose_name='Senha',
        max_length=128,           # Tamanho padrão para senhas criptografadas
        help_text="Senha para acesso ao sistema"
    )
    
    data_cadastro = models.DateTimeField(
        verbose_name='Data de Cadastro',
        auto_now_add=True,        # Preenche automaticamente quando o registro é criado
        help_text="Data e hora em que o usuário se cadastrou"
    )
    
    ativo = models.BooleanField(
        verbose_name='Usuário Ativo',
        default=True,             # Por padrão, todo usuário novo é ativo
        help_text="Determina se o usuário pode fazer apostas. Desmarque para desativar."
    )
    
    chave_pix = models.CharField(
        verbose_name= 'chave pix',
        max_length=128, 
        help_text=' Chave pix para o pagamento dos ganhadores '
    )
    
    # ===== CONFIGURAÇÕES DA CLASSE =====
    class Meta:
        verbose_name = 'Usuário'          # Nome singular no admin
        verbose_name_plural = 'Usuários'  # Nome plural no admin
        ordering = ['nome']               # Ordena os registros por nome por padrão
        db_table = 'core_usuario'         # Nome da tabela no banco (opcional)
    
    # ===== MÉTODOS =====
    
    def __str__(self):
        """
        Representação em string do objeto.
        Aparece em listas, admin, e quando você faz print(usuario)
        """
        return f"{self.nome} "
    
    def get_telefone_formatado(self):
        """
        Retorna o telefone formatado para exibição.
        Exemplo: 61999887766 vira (61) 99988-7766
        """
        if len(self.telefone) == 11:
            return f"({self.telefone[:2]}) {self.telefone[2:7]}-{self.telefone[7:]}"
        elif len(self.telefone) == 10:
            return f"({self.telefone[:2]}) {self.telefone[2:6]}-{self.telefone[6:]}"
        return self.telefone
    
    def pode_apostar(self):
        """
        Verifica se o usuário pode fazer apostas.
        Útil para validações nas views.
        """
        return self.ativo
    
    def set_senha(self, senha_texto):
        """
        Define uma nova senha (criptografada).
        Use este método em vez de definir self.senha diretamente.
        """
        self.senha = make_password(senha_texto)
    
    def check_senha(self, senha_texto):
        """
        Verifica se a senha informada está correta.
        Retorna True se a senha estiver correta, False caso contrário.
        """
        return check_password(senha_texto, self.senha)