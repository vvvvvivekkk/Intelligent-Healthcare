"""Seed database with initial data."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from backend.utils.database import init_db, execute_db, query_db


def seed():
    print("Initializing database...")
    init_db()

    # Seed Admins (New Feature)
    print("Seeding admins...")
    from backend.services.auth_service import AuthService
    AuthService.create_admin('admin', 'admin123')
    AuthService.create_admin('sysadmin', 'secureStrong!23')

    # Check if doctors seeded
    existing = query_db('SELECT COUNT(*) as c FROM doctors', one=True)
    if existing and existing['c'] > 0:
        print("Doctor data already seeded. Skipping doctors.")
        return

    print("Seeding doctors...")
    password_hash = generate_password_hash('doctor123', method='pbkdf2:sha256')

    doctors = [
        ('DOC-CARD001', 'Dr. Sarah Mitchell', 'sarah.mitchell@medsync.com', '+1-555-0101',
         password_hash, 'Cardiology', 15, 'City Heart Hospital',
         'Board-certified cardiologist specializing in interventional cardiology and heart failure management.', 1, 4.8),
        ('DOC-NEUR001', 'Dr. James Chen', 'james.chen@medsync.com', '+1-555-0102',
         password_hash, 'Neurology', 12, 'NeuroHealth Center',
         'Neurologist with expertise in headache disorders, epilepsy, and neurodegenerative diseases.', 1, 4.7),
        ('DOC-DERM001', 'Dr. Priya Sharma', 'priya.sharma@medsync.com', '+1-555-0103',
         password_hash, 'Dermatology', 10, 'SkinCare Clinic',
         'Dermatologist specializing in medical and cosmetic dermatology, skin cancer screening.', 1, 4.9),
        ('DOC-ORTH001', 'Dr. Michael Brown', 'michael.brown@medsync.com', '+1-555-0104',
         password_hash, 'Orthopedics', 18, 'Joint & Spine Center',
         'Orthopedic surgeon specializing in sports medicine and joint replacement surgery.', 1, 4.6),
        ('DOC-PEDI001', 'Dr. Emily Davis', 'emily.davis@medsync.com', '+1-555-0105',
         password_hash, 'Pediatrics', 8, 'Children\'s Wellness Clinic',
         'Pediatrician focused on preventive care, developmental assessments, and childhood illnesses.', 1, 4.8),
        ('DOC-GAST001', 'Dr. Robert Wilson', 'robert.wilson@medsync.com', '+1-555-0106',
         password_hash, 'Gastroenterology', 14, 'Digestive Health Institute',
         'Gastroenterologist specializing in IBD, liver diseases, and advanced endoscopic procedures.', 1, 4.5),
        ('DOC-PULM001', 'Dr. Lisa Anderson', 'lisa.anderson@medsync.com', '+1-555-0107',
         password_hash, 'Pulmonology', 11, 'Breathing Care Center',
         'Pulmonologist with expertise in asthma, COPD, and interstitial lung diseases.', 1, 4.7),
        ('DOC-ENDO001', 'Dr. Raj Patel', 'raj.patel@medsync.com', '+1-555-0108',
         password_hash, 'Endocrinology', 13, 'Diabetes & Hormone Center',
         'Endocrinologist specializing in diabetes management, thyroid disorders, and hormonal imbalances.', 1, 4.6),
        ('DOC-PSYC001', 'Dr. Amanda Foster', 'amanda.foster@medsync.com', '+1-555-0109',
         password_hash, 'Psychiatry', 9, 'Mental Wellness Institute',
         'Psychiatrist specializing in anxiety, depression, PTSD, and cognitive behavioral therapy.', 1, 4.8),
        ('DOC-OPTH001', 'Dr. David Kim', 'david.kim@medsync.com', '+1-555-0110',
         password_hash, 'Ophthalmology', 16, 'Vision Care Center',
         'Ophthalmologist specializing in cataract surgery, glaucoma treatment, and retinal disorders.', 1, 4.7),
        ('DOC-ENT001', 'Dr. Maria Garcia', 'maria.garcia@medsync.com', '+1-555-0111',
         password_hash, 'ENT', 10, 'Ear Nose Throat Specialists',
         'ENT specialist with expertise in sinus disorders, hearing loss, and head & neck surgery.', 1, 4.5),
        ('DOC-GENM001', 'Dr. Thomas Lee', 'thomas.lee@medsync.com', '+1-555-0112',
         password_hash, 'General Medicine', 20, 'HealthFirst Primary Care',
         'Experienced general practitioner providing comprehensive primary care and health screenings.', 1, 4.9),
    ]

    for doc in doctors:
        execute_db(
            '''INSERT INTO doctors (doctor_id, full_name, email, phone, password_hash,
               specialization, experience_years, hospital, bio, verified, rating)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            doc
        )

    print(f"  Seeded {len(doctors)} doctors")

    # Seed disease-specialization mappings
    print("Seeding disease-specialization mappings...")
    mappings = [
        ('Heart Disease', 'Cardiology', 'Coronary artery disease, heart failure, arrhythmia'),
        ('Hypertension', 'Cardiology', 'High blood pressure management'),
        ('Chest Pain', 'Cardiology', 'Angina, cardiac evaluation'),
        ('Arrhythmia', 'Cardiology', 'Irregular heartbeat conditions'),
        ('Migraine', 'Neurology', 'Chronic headaches and migraines'),
        ('Epilepsy', 'Neurology', 'Seizure disorders'),
        ('Stroke', 'Neurology', 'Cerebrovascular accidents'),
        ('Neuropathy', 'Neurology', 'Nerve damage and pain'),
        ('Alzheimer\'s', 'Neurology', 'Neurodegenerative memory disorders'),
        ('Eczema', 'Dermatology', 'Atopic dermatitis and skin inflammation'),
        ('Psoriasis', 'Dermatology', 'Chronic autoimmune skin condition'),
        ('Acne', 'Dermatology', 'Skin acne and scarring'),
        ('Skin Cancer', 'Dermatology', 'Melanoma and other skin cancers'),
        ('Arthritis', 'Orthopedics', 'Joint inflammation and degeneration'),
        ('Back Pain', 'Orthopedics', 'Spinal conditions and disc problems'),
        ('Fracture', 'Orthopedics', 'Bone fractures and injuries'),
        ('Sports Injury', 'Orthopedics', 'Athletic injuries and rehabilitation'),
        ('Common Cold', 'Pediatrics', 'Upper respiratory infections in children'),
        ('Childhood Asthma', 'Pediatrics', 'Pediatric respiratory conditions'),
        ('Growth Disorders', 'Pediatrics', 'Developmental and growth issues'),
        ('GERD', 'Gastroenterology', 'Gastroesophageal reflux disease'),
        ('IBS', 'Gastroenterology', 'Irritable bowel syndrome'),
        ('Liver Disease', 'Gastroenterology', 'Hepatitis, cirrhosis, fatty liver'),
        ('Ulcer', 'Gastroenterology', 'Stomach and duodenal ulcers'),
        ('Asthma', 'Pulmonology', 'Chronic respiratory condition'),
        ('COPD', 'Pulmonology', 'Chronic obstructive pulmonary disease'),
        ('Pneumonia', 'Pulmonology', 'Lung infection'),
        ('Bronchitis', 'Pulmonology', 'Bronchial inflammation'),
        ('Diabetes', 'Endocrinology', 'Type 1 and Type 2 diabetes'),
        ('Thyroid Disorder', 'Endocrinology', 'Hypothyroidism and hyperthyroidism'),
        ('Hormonal Imbalance', 'Endocrinology', 'Endocrine system disorders'),
        ('PCOS', 'Endocrinology', 'Polycystic ovary syndrome'),
        ('Depression', 'Psychiatry', 'Clinical depression and mood disorders'),
        ('Anxiety', 'Psychiatry', 'Generalized anxiety and panic disorders'),
        ('PTSD', 'Psychiatry', 'Post-traumatic stress disorder'),
        ('Insomnia', 'Psychiatry', 'Chronic sleep disorders'),
        ('Cataracts', 'Ophthalmology', 'Lens clouding requiring surgery'),
        ('Glaucoma', 'Ophthalmology', 'Increased eye pressure'),
        ('Macular Degeneration', 'Ophthalmology', 'Age-related vision loss'),
        ('Sinusitis', 'ENT', 'Chronic sinus infections'),
        ('Tonsillitis', 'ENT', 'Tonsil inflammation'),
        ('Hearing Loss', 'ENT', 'Partial or complete hearing impairment'),
        ('Fever', 'General Medicine', 'General fever and infection'),
        ('Flu', 'General Medicine', 'Influenza virus infection'),
        ('Fatigue', 'General Medicine', 'Chronic tiredness and weakness'),
        ('Allergies', 'General Medicine', 'Allergic reactions and management'),
    ]

    for disease, spec, desc in mappings:
        execute_db(
            'INSERT INTO disease_specialization_mapping (disease, specialization, description) VALUES (?, ?, ?)',
            (disease, spec, desc)
        )

    print(f"  Seeded {len(mappings)} disease mappings")

    # Seed sample slots for doctors (next 7 days)
    print("Seeding availability slots...")
    from datetime import datetime, timedelta

    slot_count = 0
    doctor_ids = query_db('SELECT id FROM doctors')

    for doc in doctor_ids:
        for day_offset in range(1, 8):
            date = (datetime.now() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            time_slots = [
                ('09:00', '09:30'), ('09:30', '10:00'), ('10:00', '10:30'),
                ('10:30', '11:00'), ('11:00', '11:30'), ('11:30', '12:00'),
                ('14:00', '14:30'), ('14:30', '15:00'), ('15:00', '15:30'),
                ('15:30', '16:00'), ('16:00', '16:30'), ('16:30', '17:00'),
            ]
            for start, end in time_slots:
                execute_db(
                    'INSERT INTO slots (doctor_id, slot_date, start_time, end_time, is_booked) VALUES (?, ?, ?, ?, 0)',
                    (doc['id'], date, start, end)
                )
                slot_count += 1

    print(f"  Seeded {slot_count} availability slots")

    # Seed a test patient
    print("Seeding test patient...")
    test_password = generate_password_hash('patient123', method='pbkdf2:sha256')
    execute_db(
        '''INSERT INTO users (patient_id, full_name, email, phone, password_hash, role)
           VALUES (?, ?, ?, ?, ?, 'patient')''',
        ('PAT-TEST0001', 'John Doe', 'patient@medsync.com', '+1-555-0001', test_password)
    )

    print("\n✓ Database seeded successfully!")
    print("\nTest Accounts:")
    print("  Patient: patient@medsync.com / patient123")
    print("  Doctor:  sarah.mitchell@medsync.com / doctor123")
    print("  (All doctors use password: doctor123)")


if __name__ == '__main__':
    seed()
