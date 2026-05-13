from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory


# creation du formulaire d'authentification
# ==========================================
# ==========================================
class LoginForm(forms.Form):
    username = forms.CharField(max_length = 30 , widget = forms.TextInput(attrs={'class':'form-control'}))
    password = forms.CharField(max_length = 200 , widget = forms.PasswordInput(attrs={'class':'form-control'}))

# creation du formulaire Utilisateurs
# ===================================
# ===================================
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


# formulaire pour attribue role 
class FonctionForm(forms.ModelForm):
    class Meta:
        model = Fonction
        fields = ['fonctionKey']
        labels = {
            'fonctionKey': 'Rôle / Poste',
                    }
        widgets = {
            'fonctionKey': forms.Select(attrs={'class': 'form-control'}),
            
        }

class ModifierUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']  # On ne garde QUE ce dont tu as besoin
        
    def __init__(self, *args, **kwargs):
        super(ModifierUserForm, self).__init__(*args, **kwargs)
        # On ajoute les classes Bootstrap pour garder ton beau design
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class PrestationForm(forms.ModelForm):
    class Meta:
        model = Prestation
        fields = ['libelle', 'categorie', 'prix']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Goutte Épaisse'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_libelle(self):
        """ Vérifie si une prestation avec ce libellé existe déjà (insensible à la casse) """
        libelle = self.cleaned_data.get('libelle')
        # On vérifie si un objet existe avec le même nom (en ignorant les majuscules/minuscules)
        # .exclude(pk=self.instance.pk) permet d'ignorer l'objet actuel si on est en train de le modifier
        if Prestation.objects.filter(libelle__iexact=libelle).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette prestation existe déjà dans votre catalogue.")
        return libelle


class ConfigurationHopitalForm(forms.ModelForm):
    class Meta:
        model = ConfigurationHopital
        fields = ['taux_usd_en_cdf']
        widgets = {
            'taux_usd_en_cdf': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: 2850.00'
            }),
        }

    def clean_taux_usd_en_cdf(self):
        taux = self.cleaned_data.get('taux_usd_en_cdf')
        if taux <= 0:
            raise forms.ValidationError("Le taux de change doit être supérieur à zéro.")
        return taux



class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Gynécologie, Radiographie...'
            }),
        }

    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        # On vérifie si un service avec ce nom existe déjà (en ignorant la casse si tu veux)
        if Service.objects.filter(nom__iexact=nom).exists():
            raise forms.ValidationError("Ce service existe déjà dans le système.")
        return nom

# ====================================================
#

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        # On exclut code_patient et created_by car ils sont gérés automatiquement
        fields = ['noms', 'sexe', 'age', 'adresse', 'telephone', 'service']
        
        widgets = {
            'noms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom, Post-nom et Prénom'
            }),
            'sexe': forms.Select(attrs={
                'class': 'form-control custom-select'
            }),
            'age': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 25 ans ou 6 mois'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +243...'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète du patient'
            }),
            'service': forms.Select(attrs={
                'class': 'form-control custom-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        # On peut personnaliser le libellé vide du menu déroulant des services
        self.fields['service'].empty_label = "Choisir le service d'orientation"

# ===========================================================================
#
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        # On exclut code_patient et created_by car ils sont gérés automatiquement dans le modèle
        fields = ['noms', 'sexe', 'age', 'adresse', 'telephone', 'service']
        
        widgets = {
            'noms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom, Post-nom et Prénom'
            }),
            'sexe': forms.Select(attrs={
                'class': 'form-control'
            }),
            'age': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 25 ans ou 8 mois'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +243...'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Adresse de résidence'
            }),
            'service': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        # Label par défaut pour la liste déroulante des services
        self.fields['service'].empty_label = "Sélectionner le service"

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        # Vérification si le téléphone existe déjà pour un autre patient
        # On exclut l'instance actuelle en cas de modification (self.instance.pk)
        if Patient.objects.filter(telephone=telephone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà attribué à un autre patient.")
        return telephone

    def clean_noms(self):
        noms = self.cleaned_data.get('noms')
        if len(noms) < 3:
            raise forms.ValidationError("Le nom complet est trop court.")
        return noms.upper() # On force le nom en majuscule pour l'uniformité

# 1. Formulaire principal de la Consultation
class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['motif_consultation', 'histoire_maladie', 'examen_physique', 'hypothese_diagnostique']
        widgets = {
            # On ajoute 'required': 'required' dans les attributs HTML
            'motif_consultation': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Pourquoi le patient consulte ?',
                'required': 'required'
            }),
            'histoire_maladie': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'required': 'required'
            }),
            'examen_physique': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'required': 'required'
            }),
            'hypothese_diagnostique': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Votre diagnostic provisoire',
                'required': 'required'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On s'assure que TOUS les champs du formulaire sont obligatoires au niveau de Django
        for field_name in self.fields:
            self.fields[field_name].required = True