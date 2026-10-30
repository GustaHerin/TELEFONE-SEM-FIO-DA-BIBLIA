# Telefone Sem Fio da Bíblia

> **"O Silêncio de Cristo, o Dedo dos Tradutores e a Verdadeira História do Debate sobre Homossexualidade e Pecado"**  
> **Autor:** Gustavo H. N. Gomes  
> **Apoio institucional:** TundraLab  

---

## 📖 Sobre a Obra

**Telefone Sem Fio da Bíblia** é uma investigação filológica e histórica independente que revisita os manuscritos originais em hebraico, aramaico e grego para examinar como passagens bíblicas cruciais foram traduzidas e interpretadas ao longo dos séculos.

* **Formato:** Livro Digital (PDF)
* **Páginas:** 97 páginas
* **Tamanho do Arquivo:** ~1.7 MB
* **Distribuição:** Gratuita e Integral

---

## 🌐 Funcionalidades da Plataforma Web

O repositório contém a aplicação web completa do livro, projetada para carregar rapidamente e funcionar sem dependências externas complexas:

1. **Página de Apresentação e Leitura (`index.html`):**
   * Interface moderna, escura e de alto contraste tipográfico.
   * Apresentação visual das capas frontal e traseira com suporte a lightbox.
   * Seção de exegese comparativa de termos originais (*arsenokoitai*, *malakoi*, etc.).
   * Linha do tempo histórica da evolução das traduções bíblicas.
   * Sistema de avaliações e comentários dos leitores.
   * Totalmente responsiva para smartphones, tablets e desktops.

2. **Servidor HTTP e API REST (`server.py`):**
   * Implementação nativa em Python (módulo padrão `http.server`), sem necessidade de instalar frameworks pesados.
   * Armazenamento leve em arquivos JSON sanitizados (`downloads.json` e `comentarios.json`).
   * Proteções de segurança ativas (cabeçalhos de segurança, sanitização HTML contra XSS, proteção anti-spam).
   * **Suporte Completo a CORS (`Access-Control-Allow-Origin: *`)**: permite que outros sites e aplicações externas consumam metadados e imagens do livro diretamente.

---

## 📁 Estrutura do Repositório

```text
├── index.html                     # Landing page principal e leitor interativo
├── server.py                      # Servidor HTTP nativo e API REST
├── Telefone_Sem_Fio_da_Biblia.pdf # Livro completo diagramado em PDF
├── downloads.json                 # Registro de contagem de downloads
├── comentarios.json               # Avaliações e resenhas dos leitores
├── capa_frente_web.jpg            # Imagem otimizada da capa frontal (Web)
├── contracapa_web.jpg             # Imagem otimizada da contracapa (Web)
├── site_logo.png / site_logo.svg  # Identidade visual e logotipo do projeto
├── tundralab_logo.png             # Logo da TundraLab
├── .gitignore                     # Arquivos ignorados pelo Git
└── README.md                      # Documentação do projeto
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
* Python 3.8 ou superior instalado.

### 1. Iniciar o Servidor
No terminal, dentro da pasta do projeto, execute:

```bash
python3 server.py
```

O servidor iniciará em `http://localhost:8080`.

### 2. Acessar a Aplicação
Abra seu navegador em:
```text
http://localhost:8080
```

---

## 📡 Documentação da API REST

A API do projeto foi projetada para ser consumida diretamente pelo site e por plataformas parceiras (como `tundralab.com.br`). Todos os endpoints respondem com cabeçalhos CORS liberados.

### 1. Informações Completas do Livro
* **Rota:** `GET /api/livro` (ou `/api/livro/info`)
* **Descrição:** Retorna metadados do livro, contagem de downloads, média de avaliações e URLs diretas para os arquivos.
* **Exemplo de Resposta:**
```json
{
  "status": "sucesso",
  "titulo": "Telefone Sem Fio da Bíblia",
  "subtitulo": "O Silêncio de Cristo, o Dedo dos Tradutores e a Verdadeira História do Debate sobre Homossexualidade e Pecado",
  "autor": "Gustavo H. N. Gomes",
  "paginas": 97,
  "formato": "PDF",
  "tamanho_arquivo": "1.7 MB",
  "ano": 2026,
  "idioma": "pt-BR",
  "downloads": 1,
  "avaliacoes": {
    "total": 1,
    "media_estrelas": 5.0
  },
  "capa": {
    "url": "http://localhost:8080/capa_frente_web.jpg",
    "api_url": "http://localhost:8080/api/livro/capa"
  },
  "contracapa": {
    "url": "http://localhost:8080/contracapa_web.jpg",
    "api_url": "http://localhost:8080/api/livro/contracapa"
  },
  "download": {
    "url": "http://localhost:8080/Telefone_Sem_Fio_da_Biblia.pdf"
  }
}
```

### 2. Imagens Diretas
* **Capa Frontal:** `GET /api/livro/capa`
  * Pode ser usada diretamente em tags `<img>`:
  ```html
  <img src="http://SEU_DOMINIO/api/livro/capa" alt="Capa do Livro" />
  ```
* **Contracapa:** `GET /api/livro/contracapa`

### 3. Contador de Downloads
* **Consultar:** `GET /api/downloads`
* **Registrar novo download:** `POST /api/downloads`

### 4. Avaliações e Comentários
* **Listar comentários:** `GET /api/comentarios`
* **Enviar avaliação:** `POST /api/comentarios`

---

## 📄 Licença e Direitos

* **Texto da Obra e Pesquisa:** © Gustavo H. N. Gomes. Distribuído gratuitamente para fins educacionais e informativos.
* **Código-Fonte e Plataforma Web:** Licenciado para livre estudo e divulgação da obra com apoio da TundraLab.
