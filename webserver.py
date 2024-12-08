import socket
import threading
import os
import mimetypes
from urllib.parse import unquote, parse_qs

class WebServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on http://{self.host}:{self.port}")

    def start(self):
        """Start the web server and accept incoming connections"""
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket):
        """Handle individual client connections"""
        try:
            # Receive client request
            request = client_socket.recv(1024).decode('utf-8')

            # Parse the first line of the request
            request_line = request.split('\n')[0].strip()
            method, path, _ = request_line.split()

            # Decode URL and remove query parameters
            path = unquote(path.split('?')[0])

            # Handle different routes
            if method == 'GET':
                response = self.handle_get_request(path)
            elif method == 'POST':
                response = self.handle_post_request(request, path)
            else:
                response = self.create_response(405, "Method Not Allowed")

            # Send response
            client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def handle_get_request(self, path):
        """Handle GET requests"""
        # Serve static files
        if path == '/':
            path = '/index.html'

        file_path = f'./www{path}'

        # Security check to prevent directory traversal
        if not os.path.normpath(file_path).startswith('./www'):
            return self.create_response(403, "Forbidden")

        try:
            # Try to read the file
            with open(file_path, 'rb') as file:
                content = file.read()

            # Determine MIME type
            mime_type = mimetypes.guess_type(file_path)[0] or 'text/plain'

            # Create successful response
            status = 200
            status_text = "OK"
            headers = [
                f"Content-Type: {mime_type}",
                f"Content-Length: {len(content)}"
            ]

            response = (
                f"HTTP/1.1 {status} {status_text}\r\n" +
                "\r\n".join(headers) +
                "\r\n\r\n"
            )
            return response.encode('utf-8') + content

        except FileNotFoundError:
            return self.create_response(404, "Not Found")
        except PermissionError:
            return self.create_response(403, "Forbidden")

    def handle_post_request(self, request, path):
        """Handle POST requests"""
        # Extract request body
        body = request.split('\r\n\r\n', 1)[-1]

        # Parse form data
        form_data = parse_qs(body)

        # Simple routing for POST requests
        if path == '/submit':
            # Process form submission
            response_content = "Form submitted successfully!\n"
            for key, value in form_data.items():
                response_content += f"{key}: {value[0]}\n"

            return self.create_response(200, "OK", response_content)

        return self.create_response(404, "Not Found")

    def create_response(self, status_code, status_text, content=""):
        """Create a standard HTTP response"""
        headers = [
            f"HTTP/1.1 {status_code} {status_text}",
            "Content-Type: text/plain",
            f"Content-Length: {len(content)}"
        ]

        return "\r\n".join(headers) + "\r\n\r\n" + content

def main():
    # Create www directory if it doesn't exist
    os.makedirs('www', exist_ok=True)

    # Create a sample index.html
    with open('www/index.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>My Simple Web Server</title>
</head>
<body>
    <h1>Welcome to My Web Server!</h1>
    <form action="/submit" method="post">
        <input type="text" name="name" placeholder="Enter your name">
        <input type="submit" value="Submit">
    </form>
</body>
</html>
""")

    # Start the web server
    server = WebServer()
    server.start()

if __name__ == "__main__":
    main()
