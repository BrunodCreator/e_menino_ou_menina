function getCookie(name) { /* Função CSRF igual à do login.html */
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

document.getElementById('logout-button').addEventListener('click', async (e) => {
    e.preventDefault();
    try {
        const response = await fetch('{% url "logout_api" %}', {
            method: 'POST', // Geralmente logout é POST por segurança
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // Envie o CSRF token
            }
        });
        const data = await response.json();
        if (response.ok) {
            alert(data.message); // Exibe mensagem de deslogado
            window.location.href = data.redirect_url; // Redireciona para a home/login
        } else {
            alert('Erro ao fazer logout: ' + (data.message || 'Desconhecido'));
        }
    } catch (error) {
        console.error('Erro de rede ou logout:', error);
        alert('Não foi possível fazer logout. Tente novamente.');
    }
});