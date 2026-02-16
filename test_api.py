"""Quick E2E test for MedSync AI API."""
import requests

BASE = 'http://localhost:5000'
s = requests.Session()

# Login
r = s.post(f'{BASE}/api/auth/login/patient', json={'email': 'patient@medsync.com', 'password': 'patient123'})
assert r.json()['success'], f"Login failed: {r.json()}"
print('✓ Patient login')

# Session check
r = s.get(f'{BASE}/api/auth/session')
assert r.json()['data']['authenticated'], "Session check failed"
print('✓ Session check')

# Get all doctors
r = s.get(f'{BASE}/api/doctors/all')
assert len(r.json()['data']) == 12, "Expected 12 doctors"
print(f"✓ All doctors: {len(r.json()['data'])}")

# Search doctors
r = s.get(f'{BASE}/api/doctors/search?q=cardio')
assert len(r.json()['data']) > 0, "Search failed"
print(f"✓ Search 'cardio': {len(r.json()['data'])} results")

# Specializations
r = s.get(f'{BASE}/api/doctors/specializations')
assert len(r.json()['data']) == 12, "Expected 12 specializations"
print(f"✓ Specializations: {len(r.json()['data'])}")

# Disease mapping
r = s.get(f'{BASE}/api/doctors/disease-mapping')
assert len(r.json()['data']) > 0, "Disease mapping empty"
print(f"✓ Disease mappings: {len(r.json()['data'])}")

# Get slots for first doctor
r = s.get(f'{BASE}/api/appointments/slots/doctor/1')
slots = r.json()['data']
assert len(slots) > 0, "No slots available"
print(f"✓ Doctor 1 slots: {len(slots)}")

# Book first available slot
slot_id = slots[0]['id']
r = s.post(f'{BASE}/api/appointments/book', json={'slot_id': slot_id})
assert r.json()['success'], f"Booking failed: {r.json()}"
apt = r.json()['data']
apt_id = apt['id']
print(f"✓ Booked appointment: {apt['appointment_id']}")

# Get patient appointments
r = s.get(f'{BASE}/api/appointments/patient')
assert len(r.json()['data']) >= 1, "No appointments found"
print(f"✓ Patient appointments: {len(r.json()['data'])}")

# Generate OTP
r = s.post(f'{BASE}/api/appointments/{apt_id}/otp/generate')
assert r.json()['success'], f"OTP gen failed: {r.json()}"
otp = r.json()['data']['otp']
print(f"✓ OTP generated: {otp}")

# Verify OTP
r = s.post(f'{BASE}/api/appointments/{apt_id}/otp/verify', json={'otp': otp})
assert r.json()['success'], f"OTP verify failed: {r.json()}"
print('✓ OTP verified')

# Cancel appointment
r = s.post(f'{BASE}/api/appointments/{apt_id}/cancel')
assert r.json()['success'], f"Cancel failed: {r.json()}"
print('✓ Appointment cancelled')

# Logout
r = s.post(f'{BASE}/api/auth/logout')
assert r.json()['success'], "Logout failed"
print('✓ Logout')

# Doctor login
r = s.post(f'{BASE}/api/auth/login/doctor', json={'email': 'sarah.mitchell@medsync.com', 'password': 'doctor123'})
assert r.json()['success'], f"Doctor login failed: {r.json()}"
print('✓ Doctor login')

# Doctor session
r = s.get(f'{BASE}/api/auth/session')
assert r.json()['data']['role'] == 'doctor', "Not doctor session"
print(f"✓ Doctor session: {r.json()['data']['full_name']}")

# Doctor slots
r = s.get(f'{BASE}/api/appointments/slots/doctor')
assert r.json()['success'], "Doctor slots failed"
print(f"✓ Doctor own slots: {len(r.json()['data'])}")

# Doctor appointments
r = s.get(f'{BASE}/api/appointments/doctor')
assert r.json()['success'], "Doctor appointments failed"
print(f"✓ Doctor appointments: {len(r.json()['data'])}")

print('\n🎉 All E2E tests passed!')
