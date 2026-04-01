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

# 3 
# ===========================================
# profil add 
# ===========================================
class ProfilAddForm(forms.ModelForm):
    class Meta :
        model = Profil
        fields = ['nomComplet','sexe','phone','adresse','fonction','service']
        widgets = {
            'nomComplet' : forms.TextInput(attrs = {'class':'form-control'}),
            'sexe' : forms.Select(attrs = {'class':'form-control'}) , 
            'phone' : forms.TextInput(attrs = {'class':'form-control'}),
            'adresse' : forms.TextInput(attrs = {'class':'form-control'}) , 
            'fonction' : forms.Select(attrs = {'class':'form-control'}) ,
            'service' : forms.Select(attrs = {'class':'form-control'})

        }

    # evite de voir d'autre service
    def __init__(self,*args , **kwargs):
        super(ProfilAddForm , self).__init__(*args,**kwargs)
        self.fields['service'].queryset = Service.objects.filter(nomService__in = ['secretariat','sous-administration','administration'])


# 4
# ==================================================
# patient add
# ==================================================
class PatientAddForm(forms.ModelForm):
    class Meta :
        model = Patient 
        fields = ['noms','sexeP','ageP','phone_responsable','adresseP','service']
        widgets = {
       'noms' : forms.TextInput(attrs = {'class':'form-control'}) , 
       'sexeP':forms.Select(attrs = {'class':'form-control'}) ,
       'phone_responsable' : forms.NumberInput(attrs = {'class':'form-control'}) , 
       'ageP' : forms.NumberInput(attrs = {'class':'form-control'}) ,
       'adresseP' : forms.TextInput(attrs = {'class':'form-control'}) , 
       'service' : forms.Select(attrs = {'class':'form-control'}) ,
       }


    def __init__(self , *args , **kwargs):
        super(PatientAddForm,self).__init__(*args,**kwargs)
        self.fields['service'].queryset = Service.objects.filter(nomService__in = ['pediatrie','gyneco','medecine interne'])

