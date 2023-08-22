from collections.abc import Callable, Iterable, Mapping
from typing import Any
from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages, auth
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes,force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import threading
import datetime
from expenses.models import Expense



class EmailThread(threading.Thread):
    def __init__(self, email) -> None:
         self.email = email
         threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)

class UsernameValidation(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only contain alphanumeric characters'}, status=400)
        if User.objects.filter(username = username).exists():
            return JsonResponse({'username_error': 'sorry username in use,choose another one '}, status=401)
        return JsonResponse({'username_valid': True})

class EmailValidation(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'email is invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'email already exists, choose other one'}, status=401)
        return JsonResponse({'email_valid': True})
        
class RegistrationView(View):
    def get(self, request):
        return render(request,'authentication/register.html')

    def post(self, request):
        
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        context ={
            'fieldValues': request.POST
        }
        
        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) <6:
                    messages.error(request,'Password too short')
                    return render(request, 'authentication/register.html', context)
                
                user = User.objects.create_user(username=username,email=email,password=password)
                user.is_active = False
                user.save()
                
                user_pk_bytes = force_bytes(user.pk)
                uidb64 = urlsafe_base64_encode(user_pk_bytes)
                
                domain = get_current_site(request).domain
                link = reverse('activate', kwargs={'uidb64':uidb64,'token':token_generator.make_token(user)})
                activate_url = 'http://'+domain+link
                
                email_body = 'Hi '+user.username+' Use this link to verify your account\n'+ activate_url
                email_subject= 'Activate your account'
                 
                email = EmailMessage(
                    email_subject,
                    email_body,
                    'from@yourdjangoapp.com',
                    [user.email],
                )

                messages.success(request, 'User created!')
                return render(request, 'authentication/register.html')
        return render(request, 'authentication/register.html')

class VerificationView(View):
    def get(self,request,uidb64,token):
        try:
            id_bytes = force_str(uidb64)
            id = urlsafe_base64_decode(id_bytes)
            user = User.objects.get(pk=id)
            # if not token_generator.check_token(user, token):
            #     return redirect('login'+'?message='+'User already activated')
            
            if user.is_active:
                messages.success(request,'Account already activated')
                return redirect('login')
            user.is_active=True
            user.save()
            messages.success(request,'Account activated succesfully')
        except Exception as ex:
            pass
        return redirect('login')

        
class LoginView(View):
    def get(self,request):
        return render(request, 'authentication/login.html')
    
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password'] 

        if username and password:
            user = auth.authenticate(username=username, password=password)
            
            if user:
                auth.login(request,user)
                messages.success(request, 'Welcome '+user.username)
                return redirect('expenses')

            messages.error(request, 'Invalid credentials or check your email to activate your account and  try again')
            return render(request, 'authentication/login.html')
        
        
        messages.error(request, 'Fill all fields')
        return render(request, 'authentication/login.html')

class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request,'You have been logout')
        return redirect('login')
    
class RequestPasswordResetEmail(View):
    def get(self, request):
        return render(request, 'authentication/reset-password.html')

    def post(self,request):
        email = request.POST['email']
        context={
            'values':request.POST
        }
        
        if not validate_email(email):
            messages.error(request, 'Please inform a valid email')
            return render(request, 'authentication/reset-password.html',context)
        
        current_site= get_current_site(request)
        user = User.objects.filter(email=email)
        
        if user.exists():
            user_pk_bytes = force_bytes(user[0].pk)
            uidb64 = urlsafe_base64_encode(user_pk_bytes)
            
            email_contents = {
                'user':user[0],
                'domain':current_site.domain,
                'uid': uidb64,
                'token': PasswordResetTokenGenerator().make_token(user[0])
            }            
            
            link = reverse('reset-new-password', kwargs={
                'uidb64':email_contents['uid'], 'token':email_contents['token']})
            email_subject = 'Password reset Instructions'
            reset_url = 'http://'+current_site.domain+link
            email_body = 'Hi there, please click on link below to reset password\n'+reset_url
            email = EmailMessage(
                email_subject,
                email_body,
                'from@yourdjangoapp.com',
                [email],
            )
            EmailThread(email).start()

        messages.success(request, 'We have sent a email to reset your password')
            
        return render(request, 'authentication/reset-password.html')

class CompletePasswordReset(View):
    def get(self,request, uidb64, token):
        context ={
            'uidb64':uidb64,
            'token':token,
        }
        try:
            user_id = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            if not PasswordResetTokenGenerator().check_token(user,token):
                messages.info(request, 'password lingk is invalid')
                return render(request, 'authentication/reset-password.html')
        except Exception as identifier:
            pass
        
        return render(request, 'authentication/set-new-password.html', context)
    
    def post(self,request,uidb64, token):
        context={
            'uidb64':uidb64,
            'token':token,
        }
        
        password = request.POST['password']
        password2 = request.POST['password2']

        if password !=password2:
            messages.error(request,'password dont match')
            return render(request, 'authentication/set-new-password.html',context)
        if len(password)<6:
            messages.error(request, 'password its too short')
            return render(request, 'authentication/set-new-password.html',context)
        
        try:
            user_id = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            
            messages.success(request, 'Password reset successfully, you can login now')
            return redirect('login')
        except Exception as identifier:
            messages.info(request, 'Something wrong try again')
        return render(request, 'authentication/set-new-password.html',context)

