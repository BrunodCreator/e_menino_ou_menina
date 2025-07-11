from django.urls import path
from . import views

urlpatterns = [
    
    path('login/', views.login_view, name='login_api'),
    path('', views.login_page, name='login_page') , # '' é a raiz do proje
      # URL para a página de apostas (após o login)
    path('apostas/', views.apostas_view, name='apostas_page'), 
    
    # URL para a API de logout (recebe POST ou GET do JS/botão)
    path('logout/', views.logout_view, name='logout'), # Adicione esta linha para o logout
    path('cadastro_usuario/', views.cadastro_usuario, name='cadastro_usuario'),
    # URL para obter os potes e odds (usada pelo JS para atualizar a tela)
    path('dados/', views.get_dados_usuario_e_odds, name='api_dados_usr_odd'),
    
    # URL para registrar uma nova aposta
    path('registrar/', views.iniciar_aposta_pix, name='iniciar_aposta_pix')
    
]