// core/static/js/cadastro.js

// Este código JavaScript será executado assim que o conteúdo do DOM estiver completamente carregado.
// Isso garante que todos os elementos HTML (formulários, inputs, etc.) estejam disponíveis antes de tentarmos manipulá-los.
document.addEventListener('DOMContentLoaded', () => {
    // 1. Obtenção de Referências aos Elementos HTML
    // É uma boa prática armazenar referências a elementos HTML que serão frequentemente usados em variáveis.
    const cadastroForm = document.getElementById('cadastroForm'); // O formulário de cadastro principal
    console.log("Elemento cadastroForm:", cadastroForm);
    console.log("Dataset do formulário:", cadastroForm.dataset);
    const cadastroURL = cadastroForm.dataset.cadastroUrl; // Recupera o valor do atributo data-cadastro-url
    console.log("Valor de cadastroURL:", cadastroURL);
    const nomeInput = document.getElementById('nome'); // Campo de input do nome
    const telefoneInput = document.getElementById('telefone'); // Campo de input do telefone
    const chavePixInput = document.getElementById('chave_pix'); // Campo de input da chave PIX
    const senhaInput = document.getElementById('senha'); // Campo de input da senha
    const confirmaSenhaInput = document.getElementById('confirma_senha'); // Campo de input de confirmação da senha
    const termosCheckbox = document.getElementById('termos-checkbox'); // Checkbox dos termos de uso

    // 2. Funções Auxiliares para Manipulação de Erros
    // Estas funções ajudam a exibir e limpar mensagens de erro no formulário.

    /**
     * Exibe uma mensagem de erro em um elemento HTML específico.
     * @param {string} elementId O ID do elemento <div> onde a mensagem de erro será exibida.
     * @param {string} message A mensagem de erro a ser exibida.
     */
    function showError(elementId, message) {
        const errorDiv = document.getElementById(elementId);
        if (errorDiv) { // Verifica se o elemento com o ID fornecido realmente existe no HTML
            errorDiv.textContent = message; // Define o texto da mensagem de erro
            errorDiv.style.display = message ? 'block' : 'none'; // Mostra o erro se houver mensagem, senão esconde
        }
    }

    /**
     * Limpa todas as mensagens de erro e a mensagem de sucesso no formulário.
     */
    function clearErrors() {
        // Seleciona todos os elementos que possuem a classe CSS 'error-message'
        const errorMessages = document.querySelectorAll('.error-message');
        // Itera sobre cada elemento de erro encontrado e o limpa
        errorMessages.forEach(msg => {
            msg.textContent = ''; // Limpa o texto da mensagem de erro
            msg.style.display = 'none'; // Esconde o elemento de erro
        });
        // Limpa e esconde a mensagem de sucesso também
        const successMessage = document.getElementById('success-message');
        if (successMessage) {
            successMessage.textContent = '';
            successMessage.style.display = 'none';
        }
    }

    // 3. Funções de Validação em Tempo Real (Event Listeners 'input' e 'change')
    // Estes listeners fornecem feedback instantâneo ao usuário enquanto ele digita ou interage com o formulário.

    // Listener para o input do telefone: remove caracteres não numéricos e limita o comprimento.
    telefoneInput.addEventListener('input', (e) => {
        // e.target.value é o valor atual do input.
        // replace(/\D/g, '') substitui tudo que NÃO FOR um dígito (\D) por uma string vazia (g = global, para todas as ocorrências).
        e.target.value = e.target.value.replace(/\D/g, ''); 
        
        // Limita o comprimento a 11 dígitos, caso o usuário cole um número maior.
        if (e.target.value.length > 11) {
            e.target.value = e.target.value.slice(0, 11); 
        }
        // Limpa a mensagem de erro do telefone enquanto o usuário digita (assume que ele está corrigindo).
        showError('telefone-error', ''); 
    });

    // Listeners para os campos de senha: valida comprimento e correspondência em tempo real.
    senhaInput.addEventListener('input', () => {
        // Valida o comprimento mínimo da senha (consistente com o backend).
        if (senhaInput.value.length < 6) {
            showError('senha-error', 'Senha deve ter pelo menos 6 caracteres.');
        } else {
            showError('senha-error', ''); // Limpa o erro se o comprimento for aceitável.
        }
        // Também verifica se a confirmação de senha corresponde, para feedback imediato.
        if (confirmaSenhaInput.value && senhaInput.value !== confirmaSenhaInput.value) {
            showError('confirma-senha-error', 'As senhas não coincidem.');
        } else {
            showError('confirma-senha-error', ''); // Limpa o erro se elas coincidirem.
        }
    });

    confirmaSenhaInput.addEventListener('input', () => {
        // Verifica se a confirmação de senha corresponde à senha digitada.
        if (senhaInput.value !== confirmaSenhaInput.value) {
            showError('confirma-senha-error', 'As senhas não coincidem.');
        } else {
            showError('confirma-senha-error', ''); // Limpa o erro.
        }
    });

    // Listener para o checkbox dos termos de uso.
    termosCheckbox.addEventListener('change', () => {
        // Se o checkbox for marcado, limpa a mensagem de erro dos termos.
        if (termosCheckbox.checked) {
            showError('termos-error', ''); 
        }
    });

    // 4. Tratamento do Envio do Formulário (Event Listener 'submit')
    // Este é o coração da lógica de envio de dados para o backend via AJAX.
    cadastroForm.addEventListener('submit', async (e) => {
        e.preventDefault();  // IMPEDE O ENVIO PADRÃO DO FORMULÁRIO.
                             // Se não fosse feito, a página recarregaria e não poderíamos usar AJAX.
        clearErrors();       // Limpa todas as mensagens de erro e sucesso anteriores antes de uma nova tentativa de envio.

        // 5. Validações de Frontend Antes do Envio AJAX
        // Coleta os valores atuais dos campos e realiza validações básicas.
        let hasFrontendError = false; // Flag para indicar se há algum erro de validação no frontend.

        const nome = nomeInput.value.trim(); // .trim() remove espaços em branco extras.
        const telefone = telefoneInput.value.trim();
        const chavePix = chavePixInput.value.trim();
        const senha = senhaInput.value;
        const confirmaSenha = confirmaSenhaInput.value;
        const termosAceitos = termosCheckbox.checked; // .checked retorna true/false para o estado do checkbox.

        // Validação do Nome
        if (!nome) { // Se o nome estiver vazio
            showError('nome-error', 'Nome é obrigatório.');
            hasFrontendError = true;
        }
        
        // Validação do Telefone (AGORA PARA EXATOS 11 DÍGITOS)
        // Regex para validar exatamente 11 dígitos numéricos do início ao fim da string.
        const telefoneRegex = /^\d{11}$/; 
        if (!telefone) { // Se o telefone estiver vazio
            showError('telefone-error', 'Telefone é obrigatório.');
            hasFrontendError = true;
        } else if (!telefoneRegex.test(telefone)) { // Se o telefone não corresponder ao padrão Regex
            showError('telefone-error', 'Telefone inválido. Digite 11 dígitos numéricos (DDD+9xxxx-xxxx).');
            hasFrontendError = true;
        }

        // Validação da Chave PIX
        if (!chavePix) { // Se a chave PIX estiver vazia
            showError('chave-pix-error', 'Chave PIX é obrigatória.');
            hasFrontendError = true;
        }

        // Validação da Senha
        if (!senha) { // Se a senha estiver vazia
            showError('senha-error', 'Senha é obrigatória.');
            hasFrontendError = true;
        } else if (senha.length < 6) { // Validação de comprimento mínimo
            showError('senha-error', 'Senha deve ter pelo menos 6 caracteres.');
            hasFrontendError = true;
        }

        // Validação da Confirmação de Senha
        if (senha !== confirmaSenha) { // Se a senha e a confirmação não forem iguais
            showError('confirma-senha-error', 'As senhas não coincidem.');
            // O erro na senha principal já pode ter sido exibido, mas reitera para a confirmação.
            if (!senha) { // Evita erro duplicado se a senha principal já estiver vazia
                showError('senha-error', 'As senhas não coincidem.');
            }
            hasFrontendError = true;
        }
        
        // Validação dos Termos de Uso
        if (!termosAceitos) { // Se o checkbox não estiver marcado
            showError('termos-error', 'Você deve aceitar os termos de uso.');
            hasFrontendError = true;
        }

        // Se 'hasFrontendError' for true, significa que uma ou mais validações falharam.
        // Neste caso, a função é interrompida e a requisição AJAX não é enviada ao servidor.
        if (hasFrontendError) {
            return; 
        }

        // 6. Preparação e Envio da Requisição AJAX (Fetch API)
        // Se não houver erros no frontend, prossegue com o envio dos dados.
        // FormData é uma forma fácil de coletar todos os dados de um formulário HTML,
        // incluindo inputs de texto, checkboxes, etc., e prepará-los para envio.
        const formData = new FormData(cadastroForm); 

        try {
            // fetch() é a API moderna para fazer requisições de rede no navegador.
            // Ela retorna uma Promise, por isso usamos 'async/await'.
            const response = await fetch(cadastroURL, {
                method: 'POST', // Define o método HTTP como POST.
                headers: {
                    // 'X-CSRFToken': getCookie('csrftoken') é CRÍTICO para a segurança no Django.
                    // O Django exige esse token em requisições POST para proteger contra CSRF (Cross-Site Request Forgery).
                    // getCookie() é uma função auxiliar (geralmente definida separadamente ou aqui)
                    // que lê o token CSRF de um cookie do navegador.
                    'X-CSRFToken': getCookie('csrftoken') 
                },
                // body: formData envia os dados do formulário no formato 'multipart/form-data'.
                // O navegador automaticamente define o Content-Type apropriado quando formData é usado.
                body: formData 
            });

            // await response.json() tenta parsear a resposta do servidor como JSON.
            // Isso também é uma Promise.
            const data = await response.json(); 

            // 7. Tratamento da Resposta do Servidor
            // response.ok é uma propriedade da resposta fetch que é true se o status HTTP for 2xx (sucesso).
            if (response.ok) { 
                // Se a operação foi bem-sucedida (status 200-299)
                document.getElementById('success-message').textContent = data.message; // Exibe a mensagem de sucesso do servidor.
                document.getElementById('success-message').style.display = 'block'; // Torna a mensagem visível.
                
                // Redireciona o usuário após um pequeno atraso (1.5 segundos) para que ele possa ler a mensagem.
                setTimeout(() => {
                    window.location.href = data.redirect_url; // Redireciona para a URL fornecida pelo servidor.
                }, 1500); // 1500 milissegundos = 1.5 segundos
            } else { // Se a resposta não for bem-sucedida (status 4xx ou 5xx)
                if (data.errors) { // Se o servidor retornou um objeto 'errors' no JSON (ex: erros de validação)
                    // Mapeia os erros retornados pelo backend para os elementos de erro correspondentes no frontend.
                    // Isso garante que os erros do servidor também sejam exibidos corretamente.
                    if (data.errors.nome) showError('nome-error', data.errors.nome);
                    if (data.errors.telefone) showError('telefone-error', data.errors.telefone);
                    if (data.errors.chave_pix) showError('chave-pix-error', data.errors.chave_pix);
                    if (data.errors.senha) showError('senha-error', data.errors.senha);
                    if (data.errors.confirma_senha) showError('confirma-senha-error', data.errors.confirma_senha);
                    if (data.errors.termos) showError('termos-error', data.errors.termos); // Erro para termos de uso
                    if (data.errors.non_field_errors) {
                        // Erros gerais que não se referem a um campo específico podem ser exibidos no erro principal ou no primeiro campo.
                        showError('nome-error', data.errors.non_field_errors); 
                    }
                } else {
                    // Se o servidor retornou um erro, mas sem um objeto 'errors' específico (ex: erro 500 genérico).
                    showError('nome-error', 'Erro desconhecido ao tentar cadastrar.');
                }
            }
        } catch (error) {
            // 8. Tratamento de Erros de Rede ou JSON
            // Este bloco captura erros que impedem a comunicação com o servidor ou o parsing do JSON.
            console.error('Erro de rede ou JSON:', error); // Imprime o erro no console do navegador (para desenvolvedores).
            showError('nome-error', 'Não foi possível conectar ao servidor. Verifique sua conexão.'); // Mensagem amigável para o usuário.
        }
    });

    // 9. Função Auxiliar: getCookie (PARA OBTER O TOKEN CSRF)
    // Esta função é uma implementação padrão para ler um cookie do navegador.
    // O Django define um cookie 'csrftoken' que precisa ser enviado em requisições POST, PUT, DELETE, etc.
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';'); // Divide todos os cookies em um array
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim(); // Remove espaços em branco
                // Procura o cookie que começa com o nome que estamos procurando (ex: 'csrftoken=')
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    // Decodifica a parte do valor do cookie (remove %20, etc.)
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break; // Encontrou, pode sair do loop
                }
            }
        }
        return cookieValue; // Retorna o valor do cookie encontrado, ou null se não for encontrado.
    }
});
