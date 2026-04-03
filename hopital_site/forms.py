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
        self.fields['service'].queryset = Service.objects.filter(nomService__in = ['secretariat','sous-administration','administration','pediatrie','medecine interne','gyneco'])


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

# 5 
# ====================================================
# paiement fiche
# ====================================================
class PaiementFicheForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['montant_physique', 'devise']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On ajoute du style Bootstrap pour que ce soit joli
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

# 6
# ========================================================
# signe vitaux
# ========================================================
class SignesVitauxForm(forms.ModelForm):
    class Meta:
        model = SignesVitaux
        # On exclut 'patient', 'infirmier' et 'date_prelevement' car on les gère en coulisse
        fields = [
            'temperature', 'tension_arterielle', 'poids', 
            'frequence_cardiaque', 'frequence_respiratoire', 'saturation_oxygene'
        ]
        # Ajout de classes Bootstrap pour le design
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Ex: 37.5'}),
            'tension_arterielle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12/8'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'En kg'}),
            'frequence_cardiaque': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'BPM'}),
            'frequence_respiratoire': forms.NumberInput(attrs={'class': 'form-control'}),
            'saturation_oxygene': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '%'}),
        }
                 