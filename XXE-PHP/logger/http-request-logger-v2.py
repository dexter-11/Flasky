# description: logs base64 encoded data from a request
# test the app:
# send the data via curl: DATA="fakedata" && ENCODED=$(echo -n "$DATA" | base64) && curl "http://127.0.0.1:5050?data=$ENCODED"
# check http://127.0.0.1:5050/ to get the raw data from the request
# By https://github.com/greyshell

from flask import Flask, request, render_template_string
import os
import datetime
import base64
from flask_socketio import SocketIO
import re

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

LOG_FILE = "request_logs.txt"

# HTML template with WebSocket for real-time updates
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HTTP Request Logger Base64 Decoded</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .log-entry { margin-bottom: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }
        .timestamp { font-weight: bold; color: #333; }
        .ip { color: #666; }
        .raw-data { margin-top: 5px; word-break: break-all; }
        .decoded-data {
            margin-top: 5px;
            padding: 5px;
            background-color: #e0f0e0;
            border-radius: 3px;
            word-break: break-all;
            white-space: pre-wrap; /* Preserves whitespace and line breaks */
            font-family: monospace; /* Better for code display */
        }
        #status { position: fixed; top: 10px; right: 10px; background: #ddf; padding: 5px; border-radius: 3px; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Connect to WebSocket
            const socket = io();

            // Handle incoming update events
            socket.on('new_data', function() {
                console.log('New data received!');
                document.getElementById('status').textContent = 'New data received! Updating...';

                // Update the page content
                fetch(window.location.pathname)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const newDoc = parser.parseFromString(html, 'text/html');

                        // Replace the log container content
                        document.getElementById('log-container').innerHTML =
                            newDoc.getElementById('log-container').innerHTML;

                        document.getElementById('status').textContent = 'Updated: ' +
                            new Date().toLocaleTimeString();
                    })
                    .catch(error => {
                        console.error('Error updating content:', error);
                        document.getElementById('status').textContent = 'Error updating content';
                    });
            });

            // Handle connection events
            socket.on('connect', function() {
                document.getElementById('status').textContent = 'Connected and waiting for data...';
            });

            socket.on('disconnect', function() {
                document.getElementById('status').textContent = 'Disconnected. Reconnecting...';
            });
        });
    </script>
</head>
<body>
    <div id="status">Connecting...</div>
    <h1>HTTP Request Logger Base64 Decoded</h1>

    <div id="log-container">
        <h2>Log History</h2>
        {% for entry in log_entries %}
        <div class="log-entry">
            {{ entry|safe }}
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""



def decode_base64_corrupted(data):
    """Handle corrupted base64 by trying space replacements"""
    if not data or ' ' not in data:
        return "Could not decode corrupted base64 data"

    # Try different characters to replace spaces
    for char in ['g', '0', '1', '2', 'A', 'Q']:
        try:
            # Replace spaces and fix padding
            test_string = data.replace(' ', char)
            if len(test_string) % 4:
                test_string += '=' * (4 - len(test_string) % 4)

            # Decode and clean up
            decoded = base64.b64decode(test_string, validate=True).decode('utf-8', errors='replace')

            # Basic quality check - mostly printable characters
            printable_ratio = sum(1 for c in decoded if 32 <= ord(c) <= 126 or c in '\r\n\t') / len(decoded)

            if printable_ratio > 0.7 and len(decoded) > 100:
                # Clean up common issues
                cleaned = decoded.replace('\x00', '').replace('\\n', '\n').replace('<>xml', '<?xml')
                return cleaned

        except Exception:
            continue

    return "Could not decode corrupted base64 data"


def decode_base64(data):
    """Decode base64 with corruption fallback"""
    if not data:
        return ""

    try:
        # Standard decode attempt
        clean_data = data.strip()
        if len(clean_data) % 4:
            clean_data += '=' * (4 - len(clean_data) % 4)

        return base64.b64decode(clean_data, validate=True).decode('utf-8')

    except Exception:
        # Try corruption handler for any decode failure
        return decode_base64_corrupted(data)


@app.route('/', methods=['GET'])
def index():
    """Main page to display the UI"""
    # Check if there's data in the request

    file_name = data = None

    # properly parse the parameters from the url ignoring _ char
    url = request.url

    request_line = url

    # Extract fname (value between = and ___)
    fname_match = re.search(r'fname=([^_]+)___', request_line)
    fname = fname_match.group(1) if fname_match else None

    # Extract data (value after second '=' to the end, before space or HTTP version)
    data_match = re.search(r'data=([^ ]+)', request_line)
    data = data_match.group(1) if data_match else None

    file_name = fname



    # data = request.args.get('data', '')
    #file_name = request.args.get('fname', '')

    # If there's data, process it (for backward compatibility)
    if data:
        client_ip = request.remote_addr
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Decode the base64 data
        decoded_data = decode_base64(data)

        # Create log entry - FIXED: removed extra space after IP
        log_entry = f"[{timestamp}] IP: {client_ip}\nFile: {file_name}\nRaw: {data}\nBase64_Decoded: {decoded_data}\n\n"

        # Append to log file
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(log_entry)

        # Notify all connected clients
        socketio.emit('new_data')


    # Default values for page load without data - but DON'T log these
    client_ip = request.remote_addr
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    decoded_data = ""

    # Get previous log entries
    log_entries = read_log_entries()

    # Render the HTML template
    return render_template_string(
        HTML_TEMPLATE,
        timestamp=timestamp,
        client_ip=client_ip,
        data=data,
        decoded_data=decoded_data,
        log_entries=log_entries
    )


def read_log_entries():
    """Read existing log entries with robust parsing for large/complex content"""
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as log_file:
            content = log_file.read()

        entries = []

        # Split entries by looking for timestamp pattern at start of line
        # This is more reliable than splitting by double newlines
        import re

        # Find all timestamp patterns: [YYYY-MM-DD HH:MM:SS]
        timestamp_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'

        # Split content by timestamp pattern, keeping the timestamps
        parts = re.split(f'({timestamp_pattern})', content)

        # Reconstruct entries: parts[0] is before first timestamp,
        # then alternating: timestamp_match, timestamp, entry_content
        for i in range(1, len(parts), 3):
            if i + 2 < len(parts):
                timestamp_match = parts[i]  # Full [timestamp] match
                timestamp = parts[i + 1]    # Just the timestamp
                entry_content = parts[i + 2] # Everything until next timestamp

                # Reconstruct the full entry
                full_entry = timestamp_match + entry_content

                # Parse the entry using simple string operations instead of complex regex
                lines = full_entry.strip().split('\n')

                if len(lines) < 4:  # Need at least timestamp, IP, File, Raw
                    continue

                # Extract fields by line position (more reliable than regex)
                timestamp_line = lines[0] if lines[0].startswith('[') else timestamp
                # ip_line = next((line for line in lines if line.startswith('IP: ')), 'IP: unknown')
                file_line = next((line for line in lines if line.startswith('File:')), 'File: None')
                raw_line = next((line for line in lines if line.startswith('Raw:')), 'Raw: ')

                # Extract values
                try:
                    timestamp_clean = re.search(r'\[(.*?)\]', timestamp_line).group(1)
                except:
                    timestamp_clean = timestamp

                # ip = ip_line.replace('IP: ', '').strip()
                ip = 'unknown'
                for line in lines:
                    if 'IP: ' in line:
                        ip = line.split('IP: ', 1)[1].strip()
                        break


                fname = file_line.replace('File:', '').strip()
                raw_data = raw_line.replace('Raw:', '').strip()

                # Find decoded data - everything after "Base64_Decoded:" until next entry
                decoded_data = ""
                base64_idx = -1
                for idx, line in enumerate(lines):
                    if line.startswith('Base64_Decoded:'):
                        base64_idx = idx
                        break

                if base64_idx >= 0:
                    # Get everything after "Base64_Decoded:" but stop at next timestamp
                    decoded_lines = [lines[base64_idx].replace('Base64_Decoded:', '').strip()]

                    # Add subsequent lines until we hit a timestamp pattern or end of lines
                    for line in lines[base64_idx + 1:]:
                        # Stop if we hit another timestamp (start of next entry)
                        if re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]', line):
                            break
                        decoded_lines.append(line)

                    decoded_data = '\n'.join(decoded_lines).strip()

                # Convert newlines to HTML breaks for display
                decoded_data_html = decoded_data.replace('\n', '<br>') if decoded_data else ""

                # Format entry for display
                formatted_entry = f"""<div class="timestamp">[{timestamp_clean}]</div>
<div class="ip">IP: {ip}</div>
<div class="ip">File: {fname}</div>
<div class="raw-data"><strong>Raw Data:</strong> {raw_data}</div>
<div class="decoded-data"><strong>Decoded Data:</strong> {decoded_data_html}</div>"""

                entries.append(formatted_entry)

        return entries

    except Exception as e:
        print(f"[ERROR] Log parsing failed: {e}")
        return [f"<div class='log-entry'>Error parsing logs: {str(e)}</div>"]


    except Exception as e:
        print(f"[ERROR] Log parsing failed: {e}")
        return [f"<div class='log-entry'>Error parsing logs: {str(e)}</div>"]


# Also add a function to clean up the log file if it gets corrupted
def cleanup_log_file():
    # Define the filename to check for
    filename = "request_logs.txt"

    if os.path.exists(filename):
        # If it does exist, delete it
        os.remove(filename)
        print(f"The file '{filename}' has been deleted.")
    else:
        print(f"The file '{filename}' does not exist.")

if __name__ == '__main__':
    # Clean the log file before starting
    cleanup_log_file()

    # Run the Flask app with socketio
    socketio.run(app, host='0.0.0.0', port=5050, debug=True, allow_unsafe_werkzeug=True)
