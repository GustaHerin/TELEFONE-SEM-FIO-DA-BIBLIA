
import os
import sys
import json
import html
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMENTS_FILE = os.path.join(BASE_DIR, "comentarios.json")
DOWNLOADS_FILE = os.path.join(BASE_DIR, "downloads.json")
file_lock = threading.Lock()

# Inicializacao de downloads
def init_downloads_file():
    if not os.path.exists(DOWNLOADS_FILE):
        with open(DOWNLOADS_FILE, "w", encoding="utf-8") as f:
            json.dump({"total": 0}, f)

# Carregamento de downloads
def load_downloads():
    init_downloads_file()
    try:
        with open(DOWNLOADS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("total", 0))
    except Exception:
        return 0

# Salvamento de downloads
def save_downloads(total):
    with open(DOWNLOADS_FILE, "w", encoding="utf-8") as f:
        json.dump({"total": total}, f)

DEFAULT_COMMENTS = []

# Inicializacao de comentarios
def init_comments_file():
    if not os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

# Carregamento de comentarios
def load_comments():
    init_comments_file()
    try:
        with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

# Salvamento de comentarios
def save_comments(comments):
    with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

# Manipulador HTTP
class SafeBookHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    # Cabecalhos de seguranca e CORS
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    # Tratamento de pre-flight CORS
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    # Tratamento de requisicoes HEAD
    def do_HEAD(self):
        if self.path in ("/api/livro", "/api/livro/", "/api/livro/info"):
            body = json.dumps(self._obter_dados_livro(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return
        elif self.path == "/api/livro/capa":
            capa_path = os.path.join(BASE_DIR, "capa_frente_web.jpg")
            if os.path.exists(capa_path):
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(os.path.getsize(capa_path)))
                self.end_headers()
                return
        elif self.path == "/api/livro/contracapa":
            contracapa_path = os.path.join(BASE_DIR, "contracapa_web.jpg")
            if os.path.exists(contracapa_path):
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(os.path.getsize(contracapa_path)))
                self.end_headers()
                return
        elif self.path.startswith("/api/downloads") or self.path.startswith("/api/curtidas"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            return
        elif self.path.startswith("/api/comentarios"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            return
        super().do_HEAD()

    # Tratamento de requisicoes GET
    def do_GET(self):
        # API de informacoes do livro
        if self.path in ("/api/livro", "/api/livro/", "/api/livro/info"):
            self._send_json_ok(self._obter_dados_livro())
            return

        # Capa frontal direta
        if self.path == "/api/livro/capa":
            capa_path = os.path.join(BASE_DIR, "capa_frente_web.jpg")
            if os.path.exists(capa_path):
                self._send_image(capa_path, "image/jpeg")
                return
            self._send_json_error(404, "Imagem da capa não encontrada.")
            return

        # Contracapa direta
        if self.path == "/api/livro/contracapa":
            contracapa_path = os.path.join(BASE_DIR, "contracapa_web.jpg")
            if os.path.exists(contracapa_path):
                self._send_image(contracapa_path, "image/jpeg")
                return
            self._send_json_error(404, "Imagem da contracapa não encontrada.")
            return

        # Consulta de downloads
        if self.path.startswith("/api/downloads") or self.path.startswith("/api/curtidas"):
            with file_lock:
                total = load_downloads()
            self._send_json_ok({"status": "sucesso", "total": total})
            return

        # Consulta de comentarios
        if self.path.startswith("/api/comentarios"):
            with file_lock:
                comments = load_comments()
            
            comments_sorted = sorted(comments, key=lambda x: x.get("timestamp", 0), reverse=True)
            
            payload = json.dumps(comments_sorted, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(payload)
            return

        # Arquivos estaticos
        super().do_GET()

    # Tratamento de requisicoes POST
    def do_POST(self):
        # Registro de downloads
        if self.path == "/api/downloads" or self.path == "/api/curtidas":
            with file_lock:
                total = load_downloads()
                total += 1
                save_downloads(total)

            self._send_json_ok({"status": "sucesso", "total": total})
            return

        # Registro de comentarios
        if self.path == "/api/comentarios":
            # Limite de tamanho da requisicao
            try:
                content_len = int(self.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                content_len = 0

            if content_len <= 0 or content_len > 10240:
                self._send_json_error(400, "Tamanho de envio inválido ou excessivo (máx 10KB).")
                return

            try:
                raw_body = self.rfile.read(content_len).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._send_json_error(400, "Corpo de requisição JSON inválido.")
                return

            # Protecao contra robos automaticos
            trap_val = str(data.get("b_trap", "")).strip()
            if trap_val:
                self._send_json_ok({"status": "sucesso", "mensagem": "Recebido com sucesso."})
                return

            # Validacao e limpeza dos dados
            raw_nome = str(data.get("nome", "")).strip()
            raw_comentario = str(data.get("comentario", "")).strip()
            raw_estrelas = data.get("estrelas", 5)

            if not raw_nome:
                self._send_json_error(400, "O nome é obrigatório.")
                return
            if len(raw_nome) > 60:
                raw_nome = raw_nome[:60]
            safe_nome = html.escape(raw_nome)

            try:
                estrelas = int(raw_estrelas)
                if estrelas < 1 or estrelas > 5:
                    estrelas = 5
            except (ValueError, TypeError):
                estrelas = 5

            if not raw_comentario or len(raw_comentario) < 3:
                self._send_json_error(400, "A avaliação escrita deve conter pelo menos 3 caracteres.")
                return
            if len(raw_comentario) > 1000:
                raw_comentario = raw_comentario[:1000]
            safe_comentario = html.escape(raw_comentario)

            agora = datetime.now()
            data_formatada = agora.strftime("%d/%m/%Y")
            novo_id = f"rev_{int(time.time() * 1000)}"

            novo_registro = {
                "id": novo_id,
                "nome": safe_nome,
                "estrelas": estrelas,
                "comentario": safe_comentario,
                "data": data_formatada,
                "timestamp": int(time.time())
            }

            with file_lock:
                comments = load_comments()
                comments.append(novo_registro)
                if len(comments) > 500:
                    comments = comments[-500:]
                save_comments(comments)

            self._send_json_ok({
                "status": "sucesso",
                "mensagem": "Sua avaliação foi registrada com sucesso!",
                "comentario": novo_registro
            })
            return

        self._send_json_error(404, "Endpoint não encontrado.")

    # Dados completos do livro
    def _obter_dados_livro(self):
        host = self.headers.get("Host", f"localhost:{PORT}")
        proto = self.headers.get("X-Forwarded-Proto", "http")
        base_url = f"{proto}://{host}"

        with file_lock:
            total_downloads = load_downloads()
            comments = load_comments()

        total_avaliacoes = len(comments)
        if total_avaliacoes > 0:
            media_estrelas = round(sum(c.get("estrelas", 5) for c in comments) / total_avaliacoes, 1)
        else:
            media_estrelas = 5.0

        return {
            "status": "sucesso",
            "titulo": "Telefone Sem Fio da Bíblia",
            "subtitulo": "O Silêncio de Cristo, o Dedo dos Tradutores e a Verdadeira História do Debate sobre Homossexualidade e Pecado",
            "autor": "Gustavo H. N. Gomes",
            "descricao": "Uma investigação independente, filológica e equilibrada sobre os manuscritos originais em hebraico e grego acerca do debate bíblico sobre homossexualidade e pecado.",
            "paginas": 97,
            "formato": "PDF",
            "tamanho_arquivo": "1.7 MB",
            "ano": 2026,
            "idioma": "pt-BR",
            "downloads": total_downloads,
            "avaliacoes": {
                "total": total_avaliacoes,
                "media_estrelas": media_estrelas
            },
            "capa": {
                "url": f"{base_url}/capa_frente_web.jpg",
                "api_url": f"{base_url}/api/livro/capa",
                "arquivo": "capa_frente_web.jpg"
            },
            "contracapa": {
                "url": f"{base_url}/contracapa_web.jpg",
                "api_url": f"{base_url}/api/livro/contracapa",
                "arquivo": "contracapa_web.jpg"
            },
            "download": {
                "url": f"{base_url}/Telefone_Sem_Fio_da_Biblia.pdf",
                "arquivo": "Telefone_Sem_Fio_da_Biblia.pdf"
            }
        }

    # Envio de resposta JSON de sucesso
    def _send_json_ok(self, payload_dict):
        body = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    # Envio de resposta JSON de erro
    def _send_json_error(self, code, msg):
        body = json.dumps({"status": "erro", "mensagem": msg}, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    # Envio de imagem estatica
    def _send_image(self, file_path, content_type="image/jpeg"):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self._send_json_error(500, "Erro ao carregar imagem.")

# Execucao do servidor
def run():
    init_comments_file()
    init_downloads_file()
    server_address = ("", PORT)
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(server_address, SafeBookHandler)
    print(f"[OK] Servidor Seguro Ativo em http://0.0.0.0:{PORT} (Sem Banco de Dados | JSON Sanitizado)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Encerrando servidor]")
        httpd.server_close()

if __name__ == "__main__":
    run()
