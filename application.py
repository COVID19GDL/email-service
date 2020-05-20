import boto3
import os
import base64

from flask import Flask
from flask import jsonify
from flask import request

from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# EB looks for an 'app' callable by default.
app = Flask(__name__)

def send_email():
    token = request.headers.get('Authorization', '') or ''
    if request.method == 'GET':
        data = {'status': 'is working'}
        return jsonify(data), 200
    if request.method == 'POST':
        if not json_data or not token:
            data = {
                'status': 'error',
                'message': 'missing parameters'
            }
            return jsonify(data), 400

        token_string = token.split()
        if not len(token_string) == 2 or not token_string[0] == 'Token' or not token_string[1] == '523736942fa2c02ceda6b49cdf31eb16893f18267ed2e9da5e50f9148efbb7d8':
            data = {
                'status': 'error',
                'message': 'user not authorized'
            }
            return jsonify(data), 401
        json_data = request.get_json()

        if not 'to' in json_data or not 'html_body' in json_data or not 'subject' in json_data:
            data = {
                'status': 'error',
                'message': 'missing parameters'
            }
            return jsonify(data), 400

        AWS_REGION = "us-west-2"

        SENDER = "no-reply <hola@rutacovid.org>"
        RECIPIENT = json_data['to']
        SUBJECT = json_data['subject']
        BODY_HTML = json_data['html_body']           

        CHARSET = "UTF-8"

        client = boto3.client(
            'ses',
            region_name=AWS_REGION
        )

        msg = MIMEMultipart('mixed')
        msg['Subject'] = SUBJECT 
        msg['From'] = SENDER 
        msg['To'] = RECIPIENT

        msg_body = MIMEMultipart('alternative')
        htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

        msg_body.attach(htmlpart)
        msg.attach(msg_body)

        if 'attachment' in json_data:

            if not 'filename' in json_data['attachment'] or not 'file' in json_data['attachment']:
                data = {
                'status': 'error',
                'message': 'missing parameters'
                }
                return jsonify(data), 400

            filename = json_data['attachment']['filename']
            file_pdf = json_data['attachment']['file']
            file_pdf = file_pdf.encode('ascii')
            att = MIMEApplication(base64.decodestring(file_pdf))
            att.add_header('Content-Disposition', 'attachment', filename=filename)

            msg.attach(att)

        try:
            response = client.send_raw_email(
                Source=SENDER,
                Destinations=[
                    RECIPIENT
                ],
                RawMessage={
                    'Data':msg.as_string(),
                },
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            data = {'status': 'error'}
            return jsonify(data), 500
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
            data = {'status': 'success'}
            return jsonify(data), 200

app.add_url_rule('/send-email', 'send-email',  (lambda: send_email()), methods=['GET', 'POST'])

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    app.debug = False
    app.run(host='0.0.0.0')
