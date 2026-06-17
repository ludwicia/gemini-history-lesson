import http.server
import socketserver

PORT = 8000

class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index_db.html on root path '/' or '/index.html'
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index_db.html'
        super().do_GET()

def main():
    # Allow address reuse to prevent 'Port already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), StaticHandler) as httpd:
        print(f"\n=======================================================")
        print(f"  Local Static Experiment Server Running at:")
        print(f"  URL: http://localhost:{PORT}")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == '__main__':
    main()
