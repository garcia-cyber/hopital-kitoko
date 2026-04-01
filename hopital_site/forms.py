from django import forms 
from django.contrib.auth.models import User
from .models import * 


# creation du formulaire d'authentification 
# ==========================================
# ==========================================
class LoginForm(forms.Form):
    username = forms.CharField(max_length = 30 , widget = forms.TextInput(attrs={'class':'form-control'})) 
    password = forms.CharField(max_length = 200 , widget = forms.PasswordInput(attrs={'class':'form-control'})) 


# 2
# ===========================================
# employes add   
# ===========================================

class EmployeForm(forms.ModelForm):
    password = forms.CharField(max_length=200 , widget= forms.PasswordInput(attrs={'class':'form-control'}), label='mot de passe utilisateur') 

    class  Meta:
        model = User 
        fields = ['username','email','password']
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-control'}) ,
            'email': forms.EmailInput(attrs={'class':'form-control'}) ,
            
        }      

        labels = {
            'username': 'nom utilisateur' , 
            'email': 'email utilisateur' , 
            'password': 'mot de passe utilisateur' , 

        }  