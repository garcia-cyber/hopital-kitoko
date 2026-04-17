from django import forms 
from django.contrib.auth.models import User
from .models import * 
from django.core.exceptions import ValidationError


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
    password = forms.CharField(
        max_length=200, 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        label='Mot de passe utilisateur'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Nom utilisateur',
            'email': 'Email utilisateur',
        }

    # Vérification de l'username (doublon)
    def clean_username(self):
        username = self.cleaned_data.get('username')
        exists = User.objects.filter(username=username)
        
        if self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)
            
        if exists.exists():
            raise ValidationError("Ce nom d'utilisateur est déjà utilisé dans le système.")
        return username

    # Vérification de l'email (doublon)
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email: # On vérifie seulement si l'email est rempli
            exists = User.objects.filter(email=email)
            
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
                
            if exists.exists():
                raise ValidationError("Cette adresse email est déjà enregistrée.")
        return email

    # Pour hacher le mot de passe avant la sauvegarde
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Hachage sécurisé
        if commit:
            user.save()
        return user 

# 3 
# ===========================================
# profil add 
# ===========================================
class ProfilAddForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ['nomComplet', 'sexe', 'phone', 'adresse', 'fonction', 'service']
        widgets = {
            'nomComplet': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super(ProfilAddForm, self).__init__(*args, **kwargs)
        # Filtrage des services spécifiques
        self.fields['service'].queryset = Service.objects.filter(
            nomService__in=[
                'secretariat', 'sous-administration', 'administration', 
                'pediatrie', 'medecine interne', 'gyneco', 
                'laboratoire', 'pharmacie'
            ]
        )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Vérifier si le numéro existe déjà en base de données
        # On exclut l'instance actuelle si on est en train de modifier un profil existant
        exists = Profil.objects.filter(phone=phone)
        if self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)
            
        if exists.exists():
            raise ValidationError("Le numéro existe déjà dans le système.")
            
        return phone


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
        # AJOUT des deux nouveaux champs ici :
        fields = ['montant_physique', 'devise', 'mode_paiement', 'reference_transaction']
        
        # On peut ajouter des placeholders pour aider le caissier
        widgets = {
            'reference_transaction': forms.TextInput(attrs={
                'placeholder': 'Code de transaction M-Pesa (ex: PP2604...)',
            }),
            'montant_physique': forms.NumberInput(attrs={
                'placeholder': '0.00',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ta boucle magique qui met du style Bootstrap sur tout le monde
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Optionnel : On peut rendre le label plus joli
        self.fields['mode_paiement'].label = "Mode de Paiement"
        self.fields['reference_transaction'].label = "Référence de Transaction"
# class PaiementFicheForm(forms.ModelForm):
#     class Meta:
#         model = Paiement
#         fields = ['montant_physique', 'devise']
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # On ajoute du style Bootstrap pour que ce soit joli
#         for field in self.fields.values():
#             field.widget.attrs.update({'class': 'form-control'})

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
# 7
# ===========================================================
#  consultation formulaire
# ===========================================================

class ConsultationForm(forms.ModelForm):
    # On ajoute un champ spécial pour les examens (Catégorie LABO uniquement)
    examens_labo = forms.ModelMultipleChoiceField(
        queryset=Prestation.objects.filter(categorie='LABO'),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    class Meta:
        model = Consultation
        fields = ['motif', 'diagnostic']
        widgets = {
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostic': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# 8 
# =========================================================
# gestion de depense 
# =========================================================
class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ['motif', 'montant', 'devise']
        widgets = {
            'motif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Achat carburant groupe'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'devise': forms.Select(attrs={'class': 'form-control'}),
        }


# 9
# ========================================================
# modifier profil
# ========================================================
class ProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        # On exclut userProfil car on ne veut pas changer l'utilisateur lié
        exclude = ['userProfil', 'date_register']
        widgets = {
            'nomComplet': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.Select(attrs={'class': 'form-control select'}),
            'service': forms.Select(attrs={'class': 'form-control select'}),
        }
