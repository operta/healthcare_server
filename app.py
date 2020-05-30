from flask import Flask, request, jsonify, make_response
from flask_mail import Mail, Message
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from sqlite3 import Error
import simplejson as json
import random


app = Flask(__name__)
CORS(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
db = SQLAlchemy(app)



class PatientRequest(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    patient_email = db.Column(db.String, nullable=False)
    patient_id = db.Column(db.String)
    doctor_comment = db.Column(db.String)
    patient_comment = db.Column(db.String)
    is_closed = db.Column(db.Boolean, default=False)
    is_positive = db.Column(db.Boolean, default=False)
    is_suspect = db.Column(db.Boolean, default=False)
    temperature = db.Column(db.Numeric, nullable=False)
    has_cough = db.Column(db.Boolean, nullable=False)
    has_fever = db.Column(db.Boolean, nullable=False)
    has_shortness_of_breath = db.Column(db.Boolean, nullable=False)
    has_muscle_pain = db.Column(db.Boolean, nullable=False)
    has_sore_throat = db.Column(db.Boolean, nullable=False)
    has_loss_of_ts = db.Column(db.Boolean, nullable=False)
    has_contact_with_coronac = db.Column(db.Boolean, nullable=False)
    has_recommendation = db.Column(db.Boolean)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'patient_email': self.patient_email,
            'patient_id': self.patient_id,
            'doctorComment': self.doctor_comment,
            'patientComment': self.patient_comment,
            'isClosed': self.is_closed,
            'isPositive': self.is_positive,
            'isSuspect': self.is_suspect,
            'temperature': json.dumps(self.temperature),
            'hasCough': self.has_cough,
            'hasFever': self.has_fever,
            'hasRecommendation': self.has_recommendation,
            'hasShortnessOfBreath': self.has_shortness_of_breath,
            'hasMusclePain': self.has_muscle_pain,
            'hasSoreThroat': self.has_sore_throat,
            'hasLossOfTasteOrSmell': self.has_loss_of_ts,
            'hasContactWithCoronaCase': self.has_contact_with_coronac
        }

    def is_corona_suspect(self):
        if (self.temperature > 38) and  (self.has_cough or self.has_sore_throat or self.has_muscle_pain or self.has_shortness_of_breath or self.has_contact_with_coronac or self.has_loss_of_ts):
            return True
        if self.has_contact_with_coronac and (self.has_cough or self.has_sore_throat or self.has_muscle_pain or self.has_shortness_of_breath or self.has_contact_with_coronac or self.has_loss_of_ts or self.has_fever):
            return True

        positive_suspections = 0

        if self.has_fever: positive_suspections += 1
        if self.has_cough: positive_suspections += 1
        if self.has_shortness_of_breath: positive_suspections += 1
        if self.has_muscle_pain: positive_suspections += 1
        if self.has_sore_throat: positive_suspections += 1
        if self.has_loss_of_ts: positive_suspections += 1

        if positive_suspections > 2:
            return True

        return False


@app.route('/requests')
@cross_origin()
def get_pending_requests():
    list = []
    for r in db.session.query(PatientRequest).all():
        list.append(r.serialize)

    return make_response(jsonify(list), 200)

#TODO Zana Begoli part
@app.route('/doctor-report/<int:request_id>/<string:message>', methods=['PUT'])
@cross_origin()
def doctor_report(request_id, message):
    row = db.session.query(PatientRequest).filter_by(id=request_id).first()
    row.doctor_comment = message
    row.has_recommendation = True
    db.session.commit()

    #send message to patient
    send_email(message, recipient=row.patient_email)
    return make_response(jsonify({'success': request_id}), 200)


@app.route('/close-request/<int:request_id>', methods=['PUT'])
@cross_origin()
def close_request(request_id):
    row = db.session.query(PatientRequest).filter_by(id=request_id).first()
    row.is_closed = True
    row.is_suspect = False
    db.session.commit()
    return make_response(jsonify({'success': request_id}), 200)



# TODO Sarah liedermans part
@app.route('/simulate-test/<int:request_id>', methods=['PUT'])
@cross_origin()
def simulate_test(request_id):
    simulated_val = bool(random.getrandbits(1))
    row = db.session.query(PatientRequest).filter_by(id=request_id).first()
    row.is_positive = simulated_val
    row.is_suspect = False
    row.is_closed = True
    db.session.commit()
    if not simulated_val:
        send_email("Lab test results are negative. You don't have corona virus!", row.patient_email)
    return make_response(jsonify({'success': 'Test done'}), 200)


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
            patient_email=data['patient_email'],
            temperature=data['temperature'],
            has_cough=data['hasCough'],
            has_fever=data['hasFever'],
            has_shortness_of_breath=data['hasShortnessOfBreath'],
            has_sore_throat=data['hasSoreThroat'],
            has_muscle_pain=data['hasMusclePain'],
            has_loss_of_ts=data['hasLossOfTasteOrSmell'],
            has_contact_with_coronac=data['hasContactWithCoronaCase'],
        )

        if 'patientComment' in data:
            patient_request.patient_comment = data['patientComment']

            
        if 'patient_comment' in data:
            patient_request.patient_comment = data['patient_comment']
           

        conn = connect_to_db()
        create_requests_table(conn)
        db.create_all()

        if patient_request.is_corona_suspect():
            msg = 'You have been automatically pre-screened as possible corona suspect.' \
                  ' Request has been sent to medical team. You will be contacted shortly.'
            # send_email(msg, patient_request.patient_email)
            patient_request.is_suspect = True
            db.session.add(patient_request)
            db.session.commit()
            return make_response(jsonify({'message': msg}), 200)

        msg = "Pre-screening results are negative. You are not a corona suspect!"
        # send_email(msg, patient_request.patient_email)
        patient_request.is_closed = True
        db.session.add(patient_request)
        db.session.commit()
        return make_response(
            jsonify({'message': 'Pre-screening results are negative. You are not a corona suspect!'}), 200)

    return make_response(jsonify({'error': 'Incorrect format, send JSON'}), 400)


### MAIL SERVER

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



######## SQLITE
def connect_to_db():
    conn = None
    try:
        conn = sqlite3.connect('healthcare.db')
    except Error as e:
        app.logger.error(e)
    finally:
        if conn:
            conn.close()
    return conn


def create_requests_table(conn):
    sql = """CREATE TABLE IF NOT EXISTS patient_requests (
                id integer PRIMARY KEY,
                patient_email varchar NOT NULL,
                patient_comment varchar,
                doctor_comment varchar ,
                temperature REAL NOT NULL,
                is_closed BOOLEAN NOT NULL CHECK (is_closed IN (0,1)),
                is_suspect BOOLEAN NOT NULL CHECK (is_suspect IN (0,1)),
                is_positive BOOLEAN NOT NULL CHECK (is_positive IN (0,1)),
                has_cough BOOLEAN NOT NULL CHECK (has_cough IN (0,1)),
                has_fever BOOLEAN NOT NULL CHECK (has_fever IN (0,1)),
                has_shortness_of_breath BOOLEAN NOT NULL CHECK (has_shortness_of_breath IN (0,1)),
                has_muscle_pain BOOLEAN NOT NULL CHECK (has_muscle_pain IN (0,1)),
                has_sore_throat BOOLEAN NOT NULL CHECK (has_sore_throat IN (0,1)),
                has_loss_of_ts BOOLEAN NOT NULL CHECK (has_loss_of_ts IN (0,1)),
                has_contact_with_coronac BOOLEAN NOT NULL CHECK (has_contact_with_coronac IN (0,1))
                has_recommendation BOOLEAN CHECK (has_contact_with_coronac IN (0,1))
            );"""
    try:
        cur = conn.cursor()
        cur.execute(sql)
    except Error as e:
        app.logger.error(e)


### MODEL




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
