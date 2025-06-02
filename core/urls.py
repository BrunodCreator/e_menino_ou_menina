from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login_api'),
    path('', views.login_page, name='login_page') , # '' é a raiz do proje
      # URL para a página de apostas (após o login)
    path('apostas/', views.apostas_view, name='apostas_page'), 
    
    # URL para a API de logout (recebe POST ou GET do JS/botão)
    path('logout/', views.logout_view, name='logout_api'), # Adicione esta linha para o logout
    path('cadastro/', views.cadastro_usuario, name='cadastro_usuario')
]



