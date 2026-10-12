import base64
import csv
import os.path
import pickle
import re
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_body_and_html(payload):
    """Recursively extract plain text and HTML content from email payload."""
    text_content = ''
    html_content = ''

    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType')
            data = part.get('body', {}).get('data')

            if mime_type == 'text/plain' and data:
                text_content += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif mime_type == 'text/html' and data:
                html_content += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                sub_text, sub_html = get_body_and_html(part)
                text_content += sub_text
                html_content += sub_html
    else:
        data = payload.get('body', {}).get('data')
        mime_type = payload.get('mimeType')
        if data:
            decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            if mime_type == 'text/html':
                html_content = decoded
            else:
                text_content = decoded

    return text_content, html_content


def extract_hyperlinks(html_content, text_content):
    """Extract URLs from HTML href attributes or plain text fallback."""
    urls = []
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = [a.get('href') for a in soup.find_all('a', href=True) if a.get('href')]
    
    if not urls and text_content:
        urls = re.findall(r'https?://[^\s>]+', text_content)
        
    return "; ".join(list(set(urls)))


def save_attachments(service, user_id, msg_id, payload, output_dir='attachments'):
    """Download email attachments locally and return a string of relative paths."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    saved_files = []

    def _walk_parts(parts):
        for part in parts:
            filename = part.get('filename')
            body = part.get('body', {})
            attachment_id = body.get('attachmentId')

            if filename and attachment_id:
                attachment = service.users().messages().attachments().get(
                    userId=user_id, messageId=msg_id, id=attachment_id
                ).execute()

                file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                
                # Prevent filename collisions
                safe_filename = f"{msg_id}_{filename}"
                file_path = os.path.join(output_dir, safe_filename)

                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                saved_files.append(file_path)

            if 'parts' in part:
                _walk_parts(part['parts'])

    if 'parts' in payload:
        _walk_parts(payload['parts'])

    return "; ".join(saved_files)


def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('gmail', 'v1', credentials=creds)

        target_subject = "Reserco: Building the research infrastructure students and universities need"
        query = f'subject:"{target_subject}"'

        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        if not messages:
            print(f'No messages found matching the subject "{target_subject}".')
            return

        csv_file_path = 'emails.csv'
        fieldnames = ['from', 'to', 'content', 'hyperlink', 'local_attachment_url']

        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for msg in messages:
                message = service.users().messages().get(userId='me', id=msg['id']).execute()
                payload = message.get('payload', {})
                headers = payload.get('headers', [])

                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                recipient = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown')

                text_content, html_content = get_body_and_html(payload)
                body_content = text_content.strip() if text_content else BeautifulSoup(html_content, 'html.parser').get_text().strip()

                hyperlinks = extract_hyperlinks(html_content, text_content)
                local_attachments = save_attachments(service, 'me', msg['id'], payload)

                writer.writerow({
                    'from': sender,
                    'to': recipient,
                    'content': body_content,
                    'hyperlink': hyperlinks,
                    'local_attachment_url': local_attachments
                })

        print(f"Successfully processed {len(messages)} message(s) and saved to {csv_file_path}.")

    except HttpError as error:
        print(f'An HTTP error occurred: {error}')


if __name__ == '__main__':
    main()