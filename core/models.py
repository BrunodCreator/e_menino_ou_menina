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



from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db.models import Sum, F

class ApostaManager(models.Manager):
    def get_queryset(self):
        # Apenas apostas válidas devem contar para o pote
        return super().get_queryset().filter(aposta_valida=True)
    

    def get_total_pote_masculino(self):
        # Agora soma diretamente o valor 'valor_para_pote'
        total = self.filter(sexo_escolha='M').aggregate(total_valor=Sum('valor_para_pote'))['total_valor']
        return total if total is not None else Decimal('0.00')
    
    def get_total_pote_feminino(self):
        # Agora soma diretamente o 'valor_para_pote'
        total = self.filter(sexo_palpite='F').aggregate(total_valor=Sum('valor_para_pote'))['total_valor']
        return total if total is not None else Decimal('0.00')
    
    def get_total_pote_geral(self):
         # Soma dos potes individuais já deduzidos
         return self.get_total_pote_masculino() + self.get_total_pote_feminino()
    
    def calcular_odds(self):
        total_masculino = self.get_total_pote_masculino()
        total_feminino = self.get_total_pote_feminino()
        total_geral = total_masculino + total_feminino
        
        if total_geral == Decimal('0.00'):
            return {'M': Decimal('1.00'), 'F': Decimal('1.00')}
        
        # Se algum pote estiver vazio, definir um valor mínimo simbólico
        min_value = Decimal('0.01')
        total_menino_calc = max(total_masculino, min_value)
        total_feminino_calc = max(total_feminino, min_value)
        
        odd_menino = (total_geral / total_menino_calc).quantize(Decimal('0.01'))
        odd_feminino = (total_geral / total_feminino_calc).quantize(Decimal('0.01'))
        
        return {'M': odd_menino, 'F': odd_feminino}
            
# --- Classe Aposta (com novo campo e sobrescrita do save) ---
class Aposta(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apostas'
    )

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]
    sexo_escolha = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        help_text="Seu palpite para o sexo do bebê: 'M' para Menino, 'F' para Feminino."
    )

    # Este é o valor BRUTO que o usuário contribuiu
    valor_aposta = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=False,
        null=False,
        default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Valor da sua contribuição (mínimo de R$0,01)."
    )

    # *** NOVO CAMPO: Valor efetivamente adicionado ao pote ***
    valor_para_pote = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'), # Será calculado no save
        # blank e null podem ser False pois sempre será calculado e salvo
        blank=True, # Permitir que não seja preenchido no formulário (será preenchido no save)
        null=True,  # Permitir NULL temporariamente para a primeira migração
        help_text="Valor líquido da contribuição após a dedução da taxa."
    )
    # *******************************************************

    data_aposta = models.DateTimeField(auto_now_add=True)

    aposta_valida = models.BooleanField(
        default=False,
        help_text="Indica se a aposta foi validada pelo administrador."
    )

    comprovante_pagamento = models.FileField(
        upload_to='comprovantes/',
        null=True,
        blank=True,
        help_text="Anexe o comprovante de pagamento (imagem ou PDF)."
    )

    objects = ApostaManager()

    class Meta:
        verbose_name = "Aposta"
        verbose_name_plural = "Apostas"
        ordering = ['-data_aposta']

    def __str__(self):
        return f"Aposta de {self.usuario.nome} - Palpite: {self.get_sexo_palpite_display()} - Valor Bruto: R${self.valor_contribuicao} - No Pote: R${self.valor_para_pote}"

    # *** Sobrescrevendo o método save() para calcular valor_para_pote ***
    def save(self, *args, **kwargs):
        # Calcula 75% do valor_contribuicao antes de salvar
        if self.valor_contribuicao is not None:
            self.valor_para_pote = (self.valor_contribuicao * Decimal('0.75')).quantize(Decimal('0.01'))
        else:
            self.valor_para_pote = Decimal('0.00') # Garante que haja um valor se contribuição for None (não deve acontecer com blank=False)

        super().save(*args, **kwargs) # Chama o método save original

    @property
    def odd_da_aposta(self):
        odds_atuais = Aposta.objects.calcular_odds()
        return odds_atuais.get(self.sexo_palpite, Decimal('1.00'))

    @property
    def retorno_potencial(self):
        # O retorno potencial é baseado no valor_contribuicao BRUTO do usuário
        # multiplicado pela odd que já reflete o pote DEDUZIDO.
        return (self.valor_contribuicao * self.odd_da_aposta).quantize(Decimal('0.01'))



