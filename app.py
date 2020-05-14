from flask import Flask, request, jsonify, make_response
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from sqlite3 import Error
import json


app = Flask(__name__)
CORS(app)
db = SQLAlchemy(app)



@app.route('/pending-requests')
def get_pending_requests():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE isClosed=0;")
        data = cursor.fetchall()
        return json.dumps(data)


@app.route('/', methods=['POST'])
def prescreening_request():
    if request.is_json:
        data = request.get_json()

        if 'patient_email' not in data:
            return make_response(jsonify({'error': 'Field patient_email does not exist'}), 400)
        if 'temperature' not in data:
            return make_response(jsonify({'error': 'Field temperature does not exist'}), 400)
        if 'hasCough' not in data:
            return make_response(jsonify({'error': 'Field hasCough does not exist'}), 400)
        if 'hasFever' not in data:
            return make_response(jsonify({'error': 'Field hasFever does not exist'}), 400)
        if 'hasShortnessOfBreath' not in data:
            return make_response(jsonify({'error': 'Field hasShortnessOfBreath does not exist'}), 400)
        if 'hasMusclePain' not in data:
            return make_response(jsonify({'error': 'Field hasMusclePain does not exist'}), 400)
        if 'hasSoreThroat' not in data:
            return make_response(jsonify({'error': 'Field hasSoreThroat does not exist'}), 400)
        if 'hasContactWithCoronaCase' not in data:
            return make_response(jsonify({'error': 'Field hasContactWithCoronaCase does not exist'}), 400)
        if 'hasLossOfTasteOrSmell' not in data:
            return make_response(jsonify({'error': 'Field hasLossOfTasteOrSmell does not exist'}), 400)

        patient_request = PatientRequest(
            data['patient_email'],
            data['temperature'],
            data['hasCough'],
            data['hasFever'],
            data['hasShortnessOfBreath'],
            data['hasMusclePain'],
            data['hasSoreThroat'],
            data['hasLossOfTasteOrSmell'],
            data['hasContactWithCoronaCase']
        )

        conn = connect_to_db()
        create_requests_table(conn)

        if patient_request.is_corona_suspect():
            msg = 'You have been automatically pre-screened as possible corona suspect.' \
                  ' Request has been sent to medical team. You will be contacted shortly.'
            send_email(msg, patient_request.patient_email)
            insert_request(patient_request)
            return make_response(jsonify({'message': msg}), 200)

        msg = "Pre-screening results are negative. You are not a corona suspect!"
        send_email(msg, patient_request.patient_email)
        patient_request.isNegative = True
        insert_request(patient_request)
        return make_response(
            jsonify({'message': 'Pre-screening results are negative. You are not a corona suspect!'}), 200)

    return make_response(jsonify({'error': 'Incorrect format, send JSON'}), 400)


app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'coronacare.tuwien@gmail.com'  # enter your email here
app.config['MAIL_DEFAULT_SENDER'] = 'coronacare.tuwien@gmail.com'  # enter your email here
app.config['MAIL_PASSWORD'] = 'CoronaCare123!'  # enter your password here
mail = Mail(app)


def send_email(message, recipient="dzanoperta2016@gmail.com"):
    msg = Message("Healthcare Server", recipients=[recipient])
    msg.body = message
    mail.send(msg)


DATABASE = 'pythonsqlite.db'


def connect_to_db():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
    except Error as e:
        app.logger.error(e)
    finally:
        if conn:
            conn.close()
    return conn


def insert_request(request):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        create_requests_table(conn)
        sql = """INSERT INTO requests(patient_email, temperature, hasCough, hasFever,
                    hasShortnessOfBreath, hasMusclePain, hasSoreThroat, hasLossOfTasteOrSmell, hasContactWithCoronaCase, isClosed)
                    VALUES(?,?,?,?,?,?,?,?,?,?)"""
        cur = conn.cursor()
        cur.execute(sql, request)
        return cur.lastrowid



def update_request(conn, request):
    # TODO
    return None





def create_requests_table(conn):
    sql = """CREATE TABLE IF NOT EXISTS requests (
                id integer PRIMARY KEY,
                patient_email text NOT NULL,
                comment text,
                temperature REAL NOT NULL,
                isClosed BOOLEAN NOT NULL CHECK (isClosed IN (0,1)),
                hasCough BOOLEAN NOT NULL CHECK (hasCough IN (0,1)),
                hasFever BOOLEAN NOT NULL CHECK (hasFever IN (0,1)),
                hasShortnessOfBreath BOOLEAN NOT NULL CHECK (hasShortnessOfBreath IN (0,1)),
                hasMusclePain BOOLEAN NOT NULL CHECK (hasMusclePain IN (0,1)),
                hasSoreThroat BOOLEAN NOT NULL CHECK (hasSoreThroat IN (0,1)),
                hasLossOfTasteOrSmell BOOLEAN NOT NULL CHECK (hasLossOfTasteOrSmell IN (0,1)),
                hasContactWithCoronaCase BOOLEAN NOT NULL CHECK (hasContactWithCoronaCase IN (0,1))
            );"""
    try:
        cur = conn.cursor()
        cur.execute(sql)
    except Error as e:
        app.logger.error(e)


class PatientRequest:

    def __init__(self,
                 patient_email,
                 temperature,
                 hasCough,
                 hasFever,
                 hasShortnessOfBreath,
                 hasMusclePain,
                 hasSoreThroat,
                 hasLossOfTasteOrSmell,
                 hasContactWithCoronaCase,
                 isClosed=False,
                 id=None,
                 comment="",
                 isNegative=False):
        self.patient_email = patient_email
        self.temperature = temperature
        self.hasCough = hasCough
        self.hasFever = hasFever
        self.hasShortnessOfBreath = hasShortnessOfBreath
        self.hasMusclePain = hasMusclePain
        self.hasSoreThroat = hasSoreThroat
        self.hasLossOfTasteOrSmell = hasLossOfTasteOrSmell
        self.hasContactWithCoronaCase = hasContactWithCoronaCase
        self.id = id
        self.comment = comment
        self.isClosed = isClosed
        self.isNegative = isNegative

    def __str__(self) -> str:
        return super().__str__()

    def is_corona_suspect(self):
        if (self.temperature > 38) and  (self.hasCough or self.hasSoreThroat or self.hasMusclePain or self.hasShortnessOfBreath or self.hasContactWithCoronaCase or self.hasLossOfTasteOrSmell):
            return True
        if self.hasContactWithCoronaCase and (self.hasCough or self.hasSoreThroat or self.hasMusclePain or self.hasShortnessOfBreath or self.hasContactWithCoronaCase or self.hasLossOfTasteOrSmell or self.hasFever):
            return True

        positiveSuspections = 0

        if self.hasFever: positiveSuspections += 1
        if self.hasCough: positiveSuspections += 1
        if self.hasShortnessOfBreath: positiveSuspections += 1
        if self.hasMusclePain: positiveSuspections += 1
        if self.hasSoreThroat: positiveSuspections += 1
        if self.hasLossOfTasteOrSmell: positiveSuspections += 1

        if positiveSuspections > 2:
            return True

        return False





if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
