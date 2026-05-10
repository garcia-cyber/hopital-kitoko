from django.shortcuts import render , redirect , get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth import authenticate , login as auth , logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm ,UserChangeForm
from django.contrib import messages
from django.db.models import Q , Sum 
from decimal import Decimal

# Create your views here.


# 1
# ======================================================================================
# PAGE D'ACCUEIL
# ======================================================================================
def home(request):
    return render(request , "front-end/index.html")

# 2
# =====================================================================
# CONNEXION DANS LE SYSTEME
# =====================================================================
def login(request):
    msg = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username = username , password = password)
            if user :
                auth(request,user)
                return redirect('dashboard')
            else:
                msg = "mot de passe erronne !!!:🤞"
    form = LoginForm()
    return render(request , 'back-end/page-login.html',{'form':form ,'msg':msg})

# 3
# ==========================================================================
# DECONNEXION
# ==========================================================================
def deco(request):
    logout(request)
    return redirect('home')

# 4
# ==========================================================================
# DASHBOARD
# ==========================================================================
@login_required
def dashboard(request):

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # compte les nombres des utilisateurs
    utilisateurs = User.objects.count()

    total_patients = Patient.objects.count()



    return render(request , 'back-end/index.html',
                  {
                  'fonctionKey': fonctionKey,
                  'utilisateurs' : utilisateurs ,
                  'total_patients' : total_patients
                  }
                  )
# 5
# ===========================================================================
# AJOUTER UTILISATEURS
# ===========================================================================
@login_required()
def employeAdd(request):
    msg = None
    if request.method =='POST':
        form = EmployeForm(request.POST)
        if form.is_valid():
            user = form.save(commit= False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # auth(request,user)

            form = EmployeForm(request.POST)
            msg = "employe enregistre "


    form = EmployeForm()
    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None


    return render(request,'back-end/employeAdd.html',{'fonctionKey':fonctionKey, 'form':form, 'msg':msg})

# 6
# ============================================================================
# LISTE DES UTILISATEURS ENREGISTRE
# ============================================================================
@login_required
def employeRead(request):

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # listes des utilisateurs
    lst_user = User.objects.all()
    context = {
        'fonctionKey' : fonctionKey ,
        'lst_user'    : lst_user ,
    }
    return render(request , 'back-end/employeRead.html' , context)

# 7 
# ============================================================================
# ATTRIBUE POSTE OU ROLE
# ============================================================================
@login_required
def attribuer_fonction(request, user_id):
    employe = get_object_or_404(User, id=user_id)
    msg = None

    if request.method == 'POST':
        form = FonctionForm(request.POST)
        if form.is_valid():
            fonction_instance = form.save(commit=False) # Changé le nom pour éviter les confusions
            fonction_instance.userKey = employe 
            fonction_instance.save()
            return redirect('employeRead') 
    else:
        form = FonctionForm()

    # Vérification de la fonction de l'utilisateur connecté
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'form': form,
        'employe': employe,
        'msg': msg, 
        'fonctionKey': fonctionKey # On passe la clé de fonction pour ton sidebar/droits
    }
    # J'ai retiré 'fonction': fonction qui causait l'erreur
    return render(request, 'back-end/employePoste.html', context)
# 8
# =================================================================================
#
# =================================================================================
@login_required
def liste_employe_poste(request):
    # Pour ton menu (récupère le rôle de l'utilisateur connecté)
    role_user = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role_user.fonctionKey.roleName if role_user else None

    # On récupère la liste de tous les employés ayant une fonction
    # select_related permet d'éviter les requêtes répétitives en base de données
    liste_postes = Fonction.objects.all().select_related('userKey', 'fonctionKey')

    context = {
        'liste_postes': liste_postes,
        'fonctionKey': fonctionKey,
    }
    return render(request, 'back-end/liste_fonctions.html', context)


# 9
# =================================================================================
# SUPPRIMER POSTE
# =================================================================================
@login_required
def supprimer_poste(request, fonction_id):
    # Supprime l'attribution du poste
    poste = get_object_or_404(Fonction, id=fonction_id)
    poste.delete()
    return redirect('liste_employe_poste')

# 10
# =================================================================================
# CHANGEMENT DU MOT DE PASSE SANS CONNAITRE LE MOT DE PASSE  
# =================================================================================
@login_required
def force_reinitialiser_pass(request, user_id):
    # On récupère l'utilisateur cible (soit soi-même, soit un employé par un admin)
    u = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # On passe l'utilisateur au formulaire
        form = SetPasswordForm(user=u, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Important : évite de déconnecter l'utilisateur si c'est son propre compte
            update_session_auth_hash(request, user)
            messages.success(request, f"Le mot de passe de {u.username} a été mis à jour.")
            return redirect('employeRead')
    else:
        form = SetPasswordForm(user=u)

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/reinitialiser_pass.html', {
        'form': form,
        'u': u ,
        'fonctionKey' : fonctionKey
    })
# 11
# ==================================================================================================
# MODIFICATION USER 
# ==================================================================================================
@login_required
def modifier_utilisateur(request, user_id):
    u = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # On lie le formulaire à l'utilisateur existant (instance=u)
        form = ModifierUserForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('employeRead')
    else:
        # Affiche le formulaire pré-rempli avec username et email uniquement
        form = ModifierUserForm(instance=u)

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/modifier_user.html', {
        'form': form,
        'u': u ,
        'fonctionKey': fonctionKey
    }) 

# 12
# ==================================================================================================
# PRESTATION ET LISTE DES PRESTATIONS 
# ==================================================================================================
@login_required
def gestion_prestations(request):
    # Tri par libellé pour Moyanoli Médicale
    prestations = Prestation.objects.all().order_by('libelle')
    
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2500.00
    
    if request.method == 'POST':
        form = PrestationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La prestation a été ajoutée avec succès.")
            return redirect('gestion_prestations')
        else:
            messages.error(request, "Erreur lors de l'ajout. Vérifiez les doublons.")
    else:
        form = PrestationForm()

    # Gestion du rôle pour la sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    context = {
        'prestations': prestations,
        'form': form,
        'taux': taux,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/prestation/list_prestation.html', context)

# 13
# ==================================================================================================
#  VUE CONFIGURATION TAUX (Modification unique) ---
# ==================================================================================================
@login_required
def modifier_taux(request):
    # On récupère le premier (et unique) objet, ou on en crée un s'il n'existe pas
    config, created = ConfigurationHopital.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        form = ConfigurationHopitalForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le taux de change a été mis à jour : 1 USD = {config.taux_usd_en_cdf} CDF")
            return redirect('modifier_taux')
    else:
        form = ConfigurationHopitalForm(instance=config)

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/prestation/config_taux.html', {'form': form, 'config': config ,'fonctionKey':fonctionKey})

# 14
# ==================================================================================================
#  MODIFICATION PRESTATION
# ==================================================================================================
@login_required
def modifier_prestation(request, pk):
    # Récupère la prestation ou renvoie une 404 si elle n'existe pas
    prestation = get_object_or_404(Prestation, pk=pk)
    
    if request.method == 'POST':
        # On passe 'instance=prestation' pour modifier l'existant au lieu d'en créer un nouveau
        form = PrestationForm(request.POST, instance=prestation)
        if form.is_valid():
            form.save()
            messages.success(request, f"La prestation '{prestation.libelle}' a été mise à jour.")
        else:
            # Récupère l'erreur du formulaire (comme le doublon) pour l'afficher
            error_msg = form.errors.as_text()
            messages.error(request, f"Modification échouée : {error_msg}")
    
    return redirect('gestion_prestations')

# 15
# ==================================================================================================
#  ENREGISTREMENT DES SERVICES
# ==================================================================================================
@login_required
def gestion_services(request):
    """Affiche la liste et gère l'ajout de nouveaux services"""
    services = Service.objects.all().order_by('-date_creation')
    
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Service '{form.cleaned_data['nom']}' ajouté avec succès.")
            return redirect('gestion_services')
    else:
        form = ServiceForm()

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/service/gestion_services.html', {
        'services': services,
        'form': form ,
        'fonctionKey': fonctionKey
    })

# 16
# ==================================================================================================
#  MODIFICATION DES SERVICES
# ==================================================================================================

@login_required
def modifier_service(request, pk):
    """Modifie un service existant"""
    service = get_object_or_404(Service, pk=pk)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service mis à jour avec succès.")
            return redirect('gestion_services')
    else:
        form = ServiceForm(instance=service)
    
    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/service/modifier_service.html', {
        'form': form,
        'service': service ,
        'fonctionKey' : fonctionKey
    })


# 17
# ==================================================================================================
#  ENREGISTREMENT DES PATIENT(E)S 
# ==================================================================================================
@login_required
def enregistrement_patient(request):
    # Récupération de tous les patients pour le tableau
    patients = Patient.objects.all().order_by('-date_creation')
    
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            # On enregistre mais on ne commit pas encore pour pouvoir lier l'utilisateur
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.save()
            
            messages.success(request, f"Patient {patient.noms} enregistré avec succès. Matricule : {patient.code_patient}")
            return redirect('enregistrement_patient')
        else:
            messages.error(request, "Erreur lors de l'enregistrement. Vérifiez les informations.")
    else:
        form = PatientForm()

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patients': patients,
        'form': form,
        'segment': 'enregistrement_patient', 
        'fonctionKey' : fonctionKey
    }

    return render(request, 'back-end/patient/enregistrement_patient.html', context)
# 18
# ==================================================================================================
#  LISTE DES PATIENT(E)S 
# ==================================================================================================
@login_required
def liste_patients(request):
    query = request.GET.get('search')
    
    if query:
        # Recherche par nom ou par matricule (code_patient)
        patients = Patient.objects.filter(
            Q(noms__icontains=query) | 
            Q(code_patient__icontains=query)
        ).order_by('-date_creation')
    else:
        patients = Patient.objects.all().order_by('-date_creation')
    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patients': patients,
        'search_query': query,
        'fonctionKey' : fonctionKey
    }
    return render(request, 'back-end/patient/liste_patients.html', context)

# 19
# ==================================================================================================
#  MODIFICATION DES PATIENT(E)S 
# ==================================================================================================
@login_required
def modifier_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"La fiche de {patient.noms} a été mise à jour.")
            return redirect('enregistrement_patient')
    else:
        form = PatientForm(instance=patient)
    
    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/patient/modifier_patient.html', {
        'form': form,
        'patient': patient ,
        'fonctionKey' : fonctionKey
    })

# 20
# ==================================================================================================
# PAIEMENT DE LA FICHE
# ==================================================================================================
@login_required
def payer_fiche(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # 0. Récupérer le taux de change
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else Decimal('2800.00') # Fallback au cas où

    # 1. Récupérer la prestation "Fiche"
    try:
        prestation_fiche = Prestation.objects.get(categorie='ADM', libelle__icontains="Fiche")
        prix_fiche_fixe = prestation_fiche.prix
    except (Prestation.DoesNotExist, Prestation.MultipleObjectsReturned):
        prestation_fiche = Prestation.objects.filter(categorie='ADM', libelle__icontains="Fiche").first()
        if not prestation_fiche:
            messages.error(request, "Erreur : La prestation 'Fiche' n'est pas configurée.")
            return redirect('detail_patient', patient_id=patient.id)
        prix_fiche_fixe = prestation_fiche.prix

    # 2. Calcul du cumul et reste à payer (en USD)
    deja_paye = Paiement.objects.filter(
        patient=patient, 
        service='FICHE'
    ).aggregate(Sum('montant_verse'))['montant_verse__sum'] or 0
    
    reste_a_payer_usd = Decimal(str(prix_fiche_fixe)) - Decimal(str(deja_paye))

    if request.method == 'POST':
        montant_saisi = Decimal(request.POST.get('montant', 0))
        devise = request.POST.get('devise')

        # Conversion du montant saisi en USD pour la vérification
        montant_en_usd = montant_saisi
        if devise == 'CDF':
            montant_en_usd = montant_saisi / taux

        # Vérification : Ne pas payer plus que le reste dû
        if montant_en_usd > (reste_a_payer_usd + Decimal('0.01')): # +0.01 pour éviter les erreurs d'arrondi
            messages.error(request, f"Erreur : Le montant ({montant_en_usd:.2f} USD) dépasse le reste à payer ({reste_a_payer_usd:.2f} USD).")
        elif montant_saisi > 0:
            Paiement.objects.create(
                patient=patient,
                service='FICHE',
                montant_verse=montant_en_usd, # On stocke toujours en USD pour la cohérence
                devise=devise,
                caissier=request.user
            )
            messages.success(request, f"Paiement de {montant_saisi} {devise} enregistré avec succès.")
            # return redirect('detail_patient', patient_id=patient.id)
            return redirect('liste_patients')

    # Préparation des infos pour le template (Conversion pour affichage)
    reste_a_payer_cdf = reste_a_payer_usd * taux
    
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patient': patient,
        'deja_paye': deja_paye,
        'reste_a_payer': reste_a_payer_usd,
        'reste_a_payer_cdf': reste_a_payer_cdf,
        'taux': taux,
        'prix_fiche': prix_fiche_fixe,
        'libelle_prestation': prestation_fiche.libelle,
        'fonctionKey': fonctionKey 
    }
    return render(request, 'back-end/finance/payer_fiche.html', context)