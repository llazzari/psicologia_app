from datetime import date, time

from data import appointment, patient
from data.models import Appointment, AppointmentStatus, Patient, PatientStatus
from service.database_manager import get_db_connection


def get_patients() -> list[Patient]:
    return [
        Patient(
            name="João Da Sigolandia Junior",
            address="Rua 1",
            contact="123456789",
            birthdate=date(2022, 1, 1),
            is_child=True,
            cpf_cnpj="123.456.789-00",
            school="Escola 1",
            tutor_cpf_cnpj="987.654.321-00",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            name="Maria da Silva Sauro",
            address="Rua 2",
            contact="987654321",
            birthdate=date(2020, 1, 1),
            is_child=False,
            cpf_cnpj="987.654.321-00",
            school="Escola 2",
            tutor_cpf_cnpj="123.456.789-00",
            status=PatientStatus.IN_TESTING,
        ),
    ]


def insert_patients() -> None:
    connection = get_db_connection()
    for patient_ in get_patients():
        patient.insert(connection, patient_)


def get_appointments(patients: list[Patient]) -> list[Appointment]:
    return [
        Appointment(
            patient_id=patients[0].id,
            patient_name=patients[0].name,
            appointment_date=date.today(),
            appointment_time=time(14, 30),
            status=AppointmentStatus.DONE,
        ),
        Appointment(
            patient_id=patients[1].id,
            patient_name=patients[1].name,
            appointment_date=date.today(),
            appointment_time=time(15, 30),
            duration=90,
            status=AppointmentStatus.DONE,
        ),
    ]


def insert_appointments() -> None:
    connection = get_db_connection()
    patients = patient.get_all(connection)
    for appt in get_appointments(patients):
        appointment.insert(connection, appt)
