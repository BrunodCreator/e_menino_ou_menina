// Função auxiliar para obter o CSRF token do cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const telefoneInput = document.getElementById('telefone');
    const senhaInput = document.getElementById('senha');
    const registerLink = document.getElementById('register-link');
    
    function showError(elementId, message) {
        const errorDiv = document.getElementById(elementId);
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    function clearMessages() {
        const errorMessages = document.querySelectorAll('.error-message');
        const successMessages = document.querySelectorAll('.success-message');
        errorMessages.forEach(msg => msg.style.display = 'none');
        successMessages.forEach(msg => msg.style.display = 'none');
    }
    
    telefoneInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '');
        if (e.target.value.length > 11) {
            e.target.value = e.target.value.slice(0, 11);
        }
        const errorDiv = document.getElementById('telefone-error');
        if (e.target.value.length >= 10) {
            errorDiv.style.display = 'none';
        }
    });
    
    loginForm.addEventListener('submit', async (e) => { // Adicionado 'async'
        e.preventDefault();
        clearMessages();
        
        const telefone = telefoneInput.value.trim();
        const senha = senhaInput.value.trim();
        
        let hasError = false;
        
        if (!telefone) {
            showError('telefone-error', 'Telefone é obrigatório');
            hasError = true;
        } else if (telefone.length < 10 || telefone.length > 11) {
            showError('telefone-error', 'Telefone deve ter 10 ou 11 dígitos');
            hasError = true;
        } else if (!/^\d+$/.test(telefone)) {
            showError('telefone-error', 'Telefone deve conter apenas números');
            hasError = true;
        }
        
        if (!senha) {
            showError('senha-error', 'Senha é obrigatória');
            hasError = true;
        } else if (senha.length < 4) {
            showError('senha-error', 'Senha deve ter pelo menos 4 caracteres');
            hasError = true;
        }
        
        if (!hasError) {
            try {
                const response = await fetch(loginUrl, {  // Agora usamos a URL armazenada na variável `loginUrl`
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') // Envie o CSRF token
                    },
                    body: JSON.stringify({ telefone, senha })
                });

                const data = await response.json();

                if (response.ok) { // response.ok é true para status 2xx
                    document.getElementById('success-message').textContent = data.message;
                    document.getElementById('success-message').style.display = 'block';
                    
                    setTimeout(() => {
                        window.location.href = data.redirect_url; // Redireciona para /apostas/
                    }, 1500); // Um pouco menos de delay
                } else {
                    // Se a resposta não for OK (ex: 400, 401), exiba os erros
                    if (data.errors) {
                        if (data.errors.telefone) showError('telefone-error', data.errors.telefone);
                        if (data.errors.senha) showError('senha-error', data.errors.senha);
                        if (data.errors.non_field_errors) showError('senha-error', data.errors.non_field_errors); // Pode ser mostrado em um lugar genérico
                    } else {
                        showError('senha-error', 'Erro desconhecido ao tentar fazer login.');
                    }
                }
            } catch (error) {
                console.error('Erro de rede ou JSON:', error);
                showError('senha-error', 'Não foi possível conectar ao servidor. Tente novamente.');
            }
        }
    });
    
    registerLink.addEventListener('click', (e) => {
        e.preventDefault();
        // Usando a URL para redirecionar para a página de cadastro
        window.location.href = cadastroUrl; // Agora usando a variável `cadastroUrl`
    });
});
