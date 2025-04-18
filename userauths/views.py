from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from userauths import forms as userauths_forms
from doctor import models as doctor_models
from patient import models as patient_models
from userauths import models as userauths_models
from .forms import SelectRoleForm
from .models import USER_TYPE 

def register_view(request):
    if request.user.is_authenticated:
        messages.success(request, "You are already logged in")
        return redirect("/")
    
    if request.method == "POST":
        form = userauths_forms.UserRegisterForm(request.POST or None)

        if form.is_valid():
            user = form.save()
            full_name = form.cleaned_data.get("full_name")
            email = form.cleaned_data.get("email")
            password1 = form.cleaned_data.get("password1")
            user_type = form.cleaned_data.get("user_type")

            user = authenticate(request, email=email, password=password1)
            print("user ========= ", user)

            if user is not None:
                login(request, user)

                if user_type == "Doctor":
                    doctor_models.Doctor.objects.create(user=user, full_name=full_name)
                else:
                    patient_models.Patient.objects.create(user=user, full_name=full_name, email=email)

                messages.success(request, "Account created successfully")
                return redirect("/")

            else:
                messages.error(request, "Authenticated failed, please try again!")

    else:
        form = userauths_forms.UserRegisterForm()

    context = {
        "form":form
    }
    return render(request, "userauths/sign-up.html", context)


def login_view(request):
    if request.user.is_authenticated:
        messages.success(request, "You are already logged in")
        return redirect("/")
    
    if request.method == "POST":
        form = userauths_forms.LoginForm(request.POST or None)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")

            try:
                user_instance = userauths_models.User.objects.get(email=email, is_active=True)
                user_authenticate = authenticate(request, email=email, password=password)

                if user_instance is not None:
                    login(request, user_authenticate)

                    messages.success(request, "Account created successfully")
                    
                    next_url = request.GET.get("next", '/')
                    return redirect(next_url)
                else:
                    messages.error(request, "Username or password does not exist!")
            except:
                messages.error(request, "User does not exist!")
    else:
        form = userauths_forms.LoginForm()
    
    context = {
        "form":form
    }
    return render(request, "userauths/sign-in.html", context)


def logout_view(request):
    logout(request)
    messages.success(request, "Logout successful")
    return redirect("userauths:sign-in")

class SelectRoleView(LoginRequiredMixin, FormView):
    template_name = 'userauths/select_role.html'
    form_class = SelectRoleForm
    success_url = '/' 

    def dispatch(self, request, *args, **kwargs):
        
        
        has_profile = False
        if request.user.user_type == "Doctor":
            has_profile = doctor_models.Doctor.objects.filter(user=request.user).exists()
        elif request.user.user_type == "Patient":
             has_profile = patient_models.Patient.objects.filter(user=request.user).exists()

        if request.user.user_type and has_profile:
            return redirect(self.get_success_url())
        
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        selected_role = form.cleaned_data['user_type']

       
        user.user_type = selected_role
        user.save()

        full_name = user.get_full_name() or user.username 

        if selected_role == "Doctor":
            doctor_models.Doctor.objects.get_or_create(
                user=user,
                defaults={'full_name': full_name}
            )
            messages.success(self.request, f"Role set to Doctor. Profile created/updated.")
        elif selected_role == "Patient":
            patient_models.Patient.objects.get_or_create(
                user=user,
                defaults={'full_name': full_name, 'email': user.email} # Patient model might need email
            )
            messages.success(self.request, f"Role set to Patient. Profile created/updated.")
        else:
             messages.warning(self.request, "Invalid role selected.")
             return self.form_invalid(form) 

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_roles'] = USER_TYPE
        return context
