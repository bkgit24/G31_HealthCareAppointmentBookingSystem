from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime

from doctor import models as doctor_models
from base import models as base_models

def get_notifications(request):
    if request.user.is_authenticated and hasattr(request.user, 'doctor'):
        try:
            doctor = doctor_models.Doctor.objects.get(user=request.user)
            notifications = doctor_models.Notification.objects.filter(doctor=doctor)
            return {'notifications': notifications}
        except doctor_models.Doctor.DoesNotExist:
            return {'notifications': []}
    return {'notifications': []}

@login_required
def dashboard(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

    appointments = base_models.Appointment.objects.filter(doctor=doctor).order_by("-id")
    notifications = doctor_models.Notification.objects.filter(doctor=doctor, seen=False).order_by("-id")

    time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(9, 18)]

    context = {
        "appointments": appointments[:5], 
        "notifications": notifications[:5], 
        "doctor": doctor,
        "time_slots": time_slots,
        "today": datetime.now().date(),
    }

    return render(request, "doctor/dashboard.html", context)

@login_required
def appointments(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointments = base_models.Appointment.objects.filter(doctor=doctor)

        time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(9, 18)]

        context = {
            "appointments": appointments,
            "time_slots": time_slots,
            "today": datetime.now().date(),
        }

        return render(request, "doctor/appointments.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def appointment_detail(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        
        medical_records = base_models.MedicalRecord.objects.filter(appointment=appointment)
        lab_tests = base_models.LabTest.objects.filter(appointment=appointment)
        prescriptions = base_models.Prescription.objects.filter(appointment=appointment)

        time_slots = [f"{hour:02d}:00 - {hour+1:02d}:00" for hour in range(9, 18)]

        context = {
            "appointment": appointment,
            "medical_records": medical_records,
            "lab_tests": lab_tests,
            "prescriptions": prescriptions,
            "time_slots": time_slots,
            "today": datetime.now().date(),
        }

        return render(request, "doctor/appointment_detail.html", context)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def cancel_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        appointment.status = "Cancelled"
        appointment.save()

        doctor_models.Notification.objects.create(
            doctor=doctor,
            appointment=appointment,
            type="Appointment Cancelled"
        )

        from patient import models as patient_models
        patient_models.Notification.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            type="Appointment Cancelled"
        )

        messages.success(request, "Appointment Cancelled Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def activate_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        appointment.status = "Scheduled"
        appointment.save()

        messages.success(request, "Appointment Re-Scheduled Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def complete_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        appointment.status = "Completed"
        appointment.save()

        doctor_models.Notification.objects.create(
            doctor=doctor,
            appointment=appointment,
            type="Appointment Completed"
        )

        from patient import models as patient_models
        patient_models.Notification.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            type="Appointment Completed"
        )

        messages.success(request, "Appointment Completed Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def add_medical_report(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        if request.method == "POST":
            diagnosis = request.POST.get("diagnosis")
            treatment = request.POST.get("treatment")
            base_models.MedicalRecord.objects.create(appointment=appointment, diagnosis=diagnosis, treatment=treatment)

        messages.success(request, "Medical Report Added Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def edit_medical_report(request, appointment_id, medical_report_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        medical_report = base_models.MedicalRecord.objects.get(id=medical_report_id, appointment=appointment)

        if request.method == "POST":
            diagnosis = request.POST.get("diagnosis")
            treatment = request.POST.get("treatment")

            medical_report.diagnosis = diagnosis
            medical_report.treatment = treatment
            medical_report.save()

        messages.success(request, "Medical Report Updated Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist, base_models.MedicalRecord.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def add_lab_test(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        if request.method == "POST":
            test_name = request.POST.get("test_name")
            description = request.POST.get("description")
            result = request.POST.get("result")

            base_models.LabTest.objects.create(appointment=appointment, test_name=test_name, description=description, result=result)

        messages.success(request, "Lab report Added Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def edit_lab_test(request, appointment_id, lab_test_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        lab_test = base_models.LabTest.objects.get(id=lab_test_id, appointment=appointment)

        if request.method == "POST":
            test_name = request.POST.get("test_name")
            description = request.POST.get("description")
            result = request.POST.get("result")

            lab_test.test_name = test_name
            lab_test.description = description
            lab_test.result = result
            lab_test.save()

        messages.success(request, "Lab Report Updated Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist, base_models.LabTest.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def add_prescription(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        if request.method == "POST":
            medications = request.POST.get("medications")
            base_models.Prescription.objects.create(medications=medications, appointment=appointment)

        messages.success(request, "Prescription Added Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def edit_prescription(request, appointment_id, prescription_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)
        prescription = base_models.Prescription.objects.get(id=prescription_id)

        if request.method == "POST":
            medications = request.POST.get("medications")
            prescription.medications = medications
            prescription.save()

        messages.success(request, "Prescription Updated Successfully")
        return redirect("doctor:appointment_detail", appointment.appointment_id)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist, base_models.Prescription.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def payments(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        payments = base_models.Billing.objects.filter(appointment__doctor=doctor)

        context = {
            "payments": payments
        }

        return render(request, "doctor/payments.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def notifications(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        notifications = doctor_models.Notification.objects.filter(doctor=doctor).order_by('-date')

        context = {
            "notifications": notifications
        }

        return render(request, "doctor/notifications.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def mark_noti_seen(request, noti_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        notification = doctor_models.Notification.objects.get(doctor=doctor, id=noti_id)
        notification.seen = True
        notification.save()
        
        messages.success(request, "Notification marked as seen")
        return redirect("doctor:notifications")
    except (doctor_models.Doctor.DoesNotExist, doctor_models.Notification.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def profile(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        
        if request.method == "POST":
            full_name = request.POST.get("full_name")
            image = request.FILES.get("image")
            mobile = request.POST.get("mobile")
            country = request.POST.get("country")
            bio = request.POST.get("bio")
            specialization = request.POST.get("specialization")
            qualifications = request.POST.get("qualifications")
            years_of_experience = request.POST.get("years_of_experience")

            doctor.full_name = full_name
            doctor.mobile = mobile
            doctor.country = country
            doctor.bio = bio
            doctor.specialization = specialization
            doctor.qualifications = qualifications
            doctor.years_of_experience = years_of_experience

            if image != None:
                doctor.image = image

            doctor.save()
            messages.success(request, "Profile updated successfully")
            return redirect("doctor:profile")

        context = {
            "doctor": doctor
        }

        return render(request, "doctor/profile.html", context)
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def clear_notifications(request):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        doctor_models.Notification.objects.filter(doctor=doctor).delete()
        messages.success(request, "All notifications have been cleared")
        return redirect("doctor:notifications")
    except doctor_models.Doctor.DoesNotExist:
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')

@login_required
def reschedule_appointment(request, appointment_id):
    try:
        doctor = doctor_models.Doctor.objects.get(user=request.user)
        appointment = base_models.Appointment.objects.get(appointment_id=appointment_id, doctor=doctor)

        if request.method == "POST":
            new_date = request.POST.get("new_date")
            new_time = request.POST.get("new_time")
            
            start_time = new_time.split(" - ")[0]
            appointment_datetime = f"{new_date} {start_time}:00"
            
            appointment.appointment_date = appointment_datetime
            appointment.save()

            messages.success(request, "Appointment rescheduled successfully.")
            return redirect("doctor:appointment_detail", appointment.appointment_id)
        
        context = {
            "appointment": appointment
        }
        return render(request, "doctor/reschedule_appointment.html", context)
    except (doctor_models.Doctor.DoesNotExist, base_models.Appointment.DoesNotExist):
        messages.warning(request, "Please complete your profile setup by confirming your role.")
        return redirect('userauths:select-role')
