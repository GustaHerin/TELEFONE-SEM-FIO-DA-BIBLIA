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

3. **Gerador Automatizado de PDF (`gerar_pdf.py`):**
   * Script Python que processa o manuscrito completo em Markdown e gera o arquivo OpenDocument (`.odt`) e PDF formatado.

---

## 📁 Estrutura do Repositório

```text
├── index.html                     # Landing page principal e leitor interativo
├── server.py                      # Servidor HTTP nativo e API REST
├── gerar_pdf.py                   # Script de compilação do manuscrito para ODT/PDF
├── Telefone_Sem_Fio_da_Biblia.pdf # Livro completo diagramado em PDF
├── Telefone_Sem_Fio_da_Biblia.odt # Documento fonte editável (LibreOffice)
├── downloads.json                 # Registro de contagem de downloads
├── comentarios.json               # Avaliações e resenhas dos leitores
├── capa_frente_web.jpg            # Imagem otimizada da capa frontal (Web)
├── contracapa_web.jpg             # Imagem otimizada da contracapa (Web)
├── capa_frente.png                # Imagem original de alta resolução da capa
├── contracapa.png                 # Imagem original de alta resolução da contracapa
├── capa_base.jpg                  # Arte conceitual base da capa
├── site_logo.png / site_logo.svg  # Identidade visual e logotipo do projeto
├── tundralab_logo.png             # Logo da TundraLab
├── documentacao/                  # Dossiê editorial e material de pesquisa
│   ├── MANUSCRITO_COMPLETO.md     # Texto integral do livro em Markdown
│   ├── BÍBLIA_DO_LIVRO.md         # Diretrizes teológicas e metodológicas
│   ├── PLANEJAMENTO_DOS_CAPÍTULOS.md # Estrutura e roteiro capitular
│   ├── CRONOLOGIA.md              # Linha temporal dos eventos e traduções
│   ├── PERSONAGENS.md             # Figuras históricas e acadêmicas citadas
│   ├── AUDITORIA_FINAL.md         # Registro de revisão textual e checagem
│   ├── QUESTÕES_PENDENTES.md      # Apontamentos e notas de pesquisa
│   ├── REGISTRO_DE_CONTINUIDADE.md# Histórico de alterações e consistência
│   └── RESUMO_DA_SESSÃO.md        # Síntese das sessões de redação
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
  * Body (JSON):
  ```json
  {
    "nome": "Seu Nome",
    "estrelas": 5,
    "comentario": "Excelente análise textual."
  }
  ```

---

## 📤 Como Fazer Upload para o GitHub

Para publicar este projeto em um novo repositório no seu GitHub, siga os passos abaixo no terminal:

```bash
# 1. Crie um novo repositório no seu GitHub (ex: telefone-sem-fio-da-biblia)

# 2. Conecte este repositório local ao seu GitHub:
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git

# 3. Defina o branch principal como main:
git branch -M main

# 4. Envie os arquivos:
git push -u origin main
```

---

## 📄 Licença e Direitos

* **Texto da Obra e Pesquisa:** © Gustavo H. N. Gomes. Distribuído gratuitamente para fins educacionais e informativos.
* **Código-Fonte e Plataforma Web:** Licenciado para livre estudo e divulgação da obra com apoio da TundraLab.
