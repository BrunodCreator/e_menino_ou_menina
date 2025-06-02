# core/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    """
    Manager customizado para criar usuários e superusuários.
    """

    def create_user(self, telefone, nome, senha=None, chave_pix=None, **extra_fields):
        """
        Cria e salva um usuário comum.
        - telefone e nome são obrigatórios.
        - senha (texto puro) será passada para set_password().
        - chave_pix é opcional.
        """
        if not telefone:
            raise ValueError("O campo 'telefone' deve ser preenchido.")
        if not nome:
            raise ValueError("O campo 'nome' deve ser preenchido.")

        # normaliza o telefone se necessário (remover espaços, traços, etc.)
        telefone = telefone.strip()

        user = self.model(telefone=telefone, nome=nome, chave_pix=chave_pix, **extra_fields)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_superuser(self, telefone, nome, senha=None, **extra_fields):
        """
        Cria e salva um superusuário com is_staff=True e is_superuser=True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # is_active já está True por padrão

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(telefone, nome, senha, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário que herda de AbstractBaseUser + PermissionsMixin.
    - Substituímos o campo 'senha' por 'password' herdado.
    - Adicionamos is_active, is_staff, is_superuser, last_login (herdados).
    """

    telefone_validator = RegexValidator(
        regex=r'^\d{9,11}',
        message="Telefone deve conter apenas números (9 ou 11 dígitos)"
    )

    telefone = models.CharField(
        verbose_name='Telefone',
        max_length=11,
        validators=[telefone_validator],
        unique=True,
        help_text="Digite apenas números, sem espaços ou símbolos (ex: 62999887766)"
    )

    nome = models.CharField(
        verbose_name='Nome Completo',
        max_length=100,
        help_text="Nome completo do participante"
    )

    # Removemos o campo 'senha = CharField(...)'
    # porque AbstractBaseUser já fornece:
    #     password = models.CharField(_('password'), max_length=128)
    # então não precisamos declará-lo novamente.
    #
    # Se quiséssemos renomear para 'senha', teríamos que
    # configurar explicitamente e redefinir toda a lógica.
    # É mais simples deixar o nome padrão 'password'.

    data_cadastro = models.DateTimeField(
        verbose_name='Data de Cadastro',
        auto_now_add=True,
        help_text="Data e hora em que o usuário se cadastrou"
    )

    ativo = models.BooleanField(
        verbose_name='Usuário Ativo',
        default=True,
        help_text="Determina se o usuário pode fazer apostas. Desmarque para desativar."
    )

    chave_pix = models.CharField(
        verbose_name='Chave PIX',
        max_length=128,
        blank=True,
        null=True,
        help_text='Chave PIX para o pagamento dos ganhadores'
    )

    # Campos obrigatórios para o Django Auth:
    is_staff = models.BooleanField(
        verbose_name='Staff Status',
        default=False,
        help_text="Define se o usuário tem acesso ao site do admin."
    )
    is_active = models.BooleanField(
        verbose_name='Active',
        default=True,
        help_text="Define se o usuário deve ser tratado como ativo. Desmarcar para desativá-lo."
    )
    # is_superuser é fornecido pelo PermissionsMixin

    # O campo last_login vem de AbstractBaseUser

    USERNAME_FIELD = 'telefone'
    REQUIRED_FIELDS = ['nome']  # além de telefone, deve informar nome

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']
        db_table = 'core_usuario'

    def __str__(self):
        return f"{self.nome}"

    def get_telefone_formatado(self):
        if len(self.telefone) == 11:
            return f"({self.telefone[:2]}) {self.telefone[2:7]}-{self.telefone[7:]}"
        elif len(self.telefone) == 10:
            return f"({self.telefone[:2]}) {self.telefone[2:6]}-{self.telefone[6:]}"
        return self.telefone

    def pode_apostar(self):
        return self.ativo
