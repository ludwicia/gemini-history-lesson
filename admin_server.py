import http.server
import socketserver
import json
import re
import os
import urllib.parse
import subprocess
import sys
import atexit
import importlib

PORT = 8001
main_server_process = None

def get_course_articles():
    try:
        with open('course_config.json', 'r', encoding='utf-8') as f:
            return json.load(f).get('articles', {})
    except Exception as e:
        print(f"Error loading course_config.json: {e}")
        return {}

def stop_main_server():
    global main_server_process
    if main_server_process is not None and main_server_process.poll() is None:
        print("Stopping main website server (Port 8000)...")
        try:
            main_server_process.terminate()
            main_server_process.wait(timeout=3)
            print("Main website server stopped successfully.")
        except Exception as e:
            print(f"Error stopping main server: {e}")
        main_server_process = None

# Automatically stop the child server when the admin server exits
atexit.register(stop_main_server)


class AdminRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to suppress standard HTTP logging to keep console clean
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)

        # 1. Serve admin.html on root path
        if parsed_url.path == '/' or parsed_url.path == '/admin.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open('admin.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
            return

        # 2. API: GET /api/status (Check if main site server is running)
        if parsed_url.path == '/api/status':
            global main_server_process
            running = main_server_process is not None and main_server_process.poll() is None
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'running': running, 'port': 8000}).encode('utf-8'))
            return

        # 3. API: GET /api/articles (Get list of article metadata & files)
        if parsed_url.path == '/api/articles':
            articles_cfg = get_course_articles()
            articles = []
            for pid, data in articles_cfg.items():
                file_path = data.get('file_path')
                articles.append({
                    'id': pid,
                    'title': data.get('title', pid),
                    'filePath': file_path
                })

            # Sort articles by page number key
            articles.sort(key=lambda x: int(re.search(r'\d+', x['id']).group()) if re.search(r'\d+', x['id']) else 0)

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'articles': articles}, ensure_ascii=False).encode('utf-8'))
            return

        # 4. API: GET /api/article?id=pageXX (Load raw Markdown content)
        if parsed_url.path == '/api/article':
            params = urllib.parse.parse_qs(parsed_url.query)
            pid = params.get('id', [''])[0].strip()

            articles_cfg = get_course_articles()
            if not pid or pid not in articles_cfg:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid article ID'}).encode('utf-8'))
                return

            file_path = articles_cfg[pid].get('file_path')

            if not file_path or not os.path.exists(file_path):
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"File not found: {file_path}"}, ensure_ascii=False).encode('utf-8'))
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response_data = {
                'id': pid,
                'title': articles_cfg[pid].get('title', pid),
                'filePath': file_path,
                'markdown': markdown_content
            }
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            return

        # Fallback to standard static file handling (for stylesheet, icons, etc.)
        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)

        # 1. API: POST /api/start (Start server.py)
        if parsed_url.path == '/api/start':
            global main_server_process
            success = False
            message = ""

            if main_server_process is not None and main_server_process.poll() is None:
                message = "伺服器已經在運行中"
                success = True
            else:
                try:
                    # Launch server.py in unbuffered mode as a background subprocess
                    # Using sys.executable guarantees it uses the same python binary
                    main_server_process = subprocess.Popen(
                        [sys.executable, '-u', 'server.py'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                    )
                    message = "本機伺服器啟動成功"
                    success = True
                    print("Started main website server on http://localhost:8000")
                except Exception as e:
                    message = f"啟動失敗: {e}"
                    success = False
                    print(f"Error starting server: {e}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}, ensure_ascii=False).encode('utf-8'))
            return

        # 2. API: POST /api/stop (Stop server.py)
        if parsed_url.path == '/api/stop':
            success = False
            message = ""

            if main_server_process is not None and main_server_process.poll() is None:
                try:
                    main_server_process.terminate()
                    main_server_process.wait(timeout=3)
                    main_server_process = None
                    message = "本機伺服器已成功關閉"
                    success = True
                    print("Stopped main website server (Port 8000).")
                except Exception as e:
                    message = f"關閉時出錯: {e}"
                    success = False
                    print(f"Error stopping server: {e}")
            else:
                message = "伺服器目前沒有在運行"
                success = True

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}, ensure_ascii=False).encode('utf-8'))
            return

        # 3. API: POST /api/compile (Trigger compilation manual rebuild)
        if parsed_url.path == '/api/compile':
            success = False
            message = ""
            try:
                res = subprocess.run([sys.executable, 'run_build.py'], capture_output=True, text=True)
                if res.returncode == 0:
                    message = "網頁、切片編譯並已同步至 Firestore！"
                    success = True
                else:
                    message = f"編譯或同步失敗: {res.stderr or res.stdout}"
                    success = False
            except Exception as e:
                message = f"編譯失敗: {e}"
                success = False
                print(f"Compile error: {e}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}, ensure_ascii=False).encode('utf-8'))
            return

        # 4. API: POST /api/article (Save markdown file & compile)
        if parsed_url.path == '/api/article':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            pid = data.get('id')
            markdown_content = data.get('markdown')

            articles_cfg = get_course_articles()
            if not pid or pid not in articles_cfg:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid article ID'}).encode('utf-8'))
                return

            file_path = articles_cfg[pid].get('file_path')

            if not file_path:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Article file path not found'}).encode('utf-8'))
                return

            try:
                # 1. Write the edited raw Markdown back to disk
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                # 2. Run the unified build pipeline
                res = subprocess.run([sys.executable, 'run_build.py'], capture_output=True, text=True)
                if res.returncode == 0:
                    success = True
                    message = "文章修改成功，且已自動編譯並同步至 Firestore！"
                    print(f"Article {pid} saved and rebuilt successfully.")
                else:
                    success = False
                    message = f"儲存成功，但編譯/同步失敗: {res.stderr or res.stdout}"
                    print(f"Article {pid} saved but build failed: {res.stderr or res.stdout}")
            except Exception as e:
                success = False
                message = f"儲存或編譯失敗: {e}"
                print(f"Error saving/building article {pid}: {e}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}, ensure_ascii=False).encode('utf-8'))
            return

        # 5. API: POST /api/preview (Render markdown to HTML)
        if parsed_url.path == '/api/preview':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            markdown_content = data.get('markdown', '')

            import markdown
            # Compile using tables and toc extensions to match build_html_md
            html_content = markdown.markdown(markdown_content, extensions=['tables', 'toc'])

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'html': html_content}, ensure_ascii=False).encode('utf-8'))
            return

        self.send_error(404, "Not Found")


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AdminRequestHandler) as httpd:
        print(f"\n=======================================================")
        print(f"  Ludwica's History Admin Console Running at:")
        print(f"  URL: http://localhost:{PORT}")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down admin server...")
            stop_main_server()

if __name__ == '__main__':
    main()
