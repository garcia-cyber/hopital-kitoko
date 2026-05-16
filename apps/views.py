from django.shortcuts import render , redirect , get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth import authenticate , login as auth_login , logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm ,UserChangeForm
from django.contrib import messages
from django.db.models import Q , Sum 
from decimal import Decimal , ROUND_HALF_UP
import pytz
from datetime import timedelta
from django.db import transaction
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


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
    # Si l'utilisateur est déjà connecté, on le redirige directement
    if request.user.is_authenticated:
         return redirect('dashboard')

    msg = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    return redirect('dashboard')
                else:
                    msg = "Votre compte est désactivé."
            else:
                msg = "Identifiants invalides. Veuillez réessayer. 🤞"
    else:
        form = LoginForm()

    # Note : On passe 'form' tel quel. Si c'est un POST invalide, 
    # il contiendra les erreurs et les données saisies.
    return render(request, 'back-end/login.html', {'form': form, 'msg': msg})

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
    # 1. Gestion de la recherche (Query)
    query = request.GET.get('q')
    if query:
        prestations_list = Prestation.objects.filter(
            Q(libelle__icontains=query) | Q(categorie__icontains=query)
        ).order_by('libelle')
    else:
        prestations_list = Prestation.objects.all().order_by('libelle')

    # 2. Récupération du taux de change
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2500.00

    # 3. Pagination (10 éléments par page)
    paginator = Paginator(prestations_list, 10)
    page_number = request.GET.get('page')
    prestations_obj = paginator.get_page(page_number)

    # 4. Calcul du prix en CDF pour les éléments de la page actuelle
    for item in prestations_obj:
        item.prix_cdf = item.prix * taux

    # 5. Gestion de l'ajout (POST)
    if request.method == 'POST':
        form = PrestationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La prestation a été ajoutée avec succès.")
            return redirect('gestion_prestations')
    else:
        form = PrestationForm()

    # 6. Gestion du rôle utilisateur
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    # 7. Préparation des catégories pour le modal de modification
    # On récupère les tuples (code, nom) définis dans les CHOICES du modèle
    categories_list = Prestation._meta.get_field('categorie').choices

    context = {
        'prestations': prestations_obj, # On passe l'objet paginé
        'form': form,
        'taux': taux,
        'fonctionKey': fonctionKey,
        'categories_list': categories_list, # Indispensable pour la boucle dans le modal
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
    prestation = get_object_or_404(Prestation, pk=pk)
    
    if request.method == 'POST':
        # L'instance permet de mettre à jour l'objet existant au lieu d'en créer un nouveau
        form = PrestationForm(request.POST, instance=prestation)
        if form.is_valid():
            form.save()
            messages.success(request, f"La prestation '{prestation.libelle}' a été mise à jour.")
        else:
            messages.error(request, "Erreur lors de la mise à jour. Vérifiez les données.")
            
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
    taux = config.taux_usd_en_cdf if config else Decimal('2800.00')

    # 1. Récupérer la prestation "Fiche"
    try:
        prestation_fiche = Prestation.objects.get(categorie='ADM', libelle__icontains="Fiche")
    except (Prestation.DoesNotExist, Prestation.MultipleObjectsReturned):
        prestation_fiche = Prestation.objects.filter(categorie='ADM', libelle__icontains="Fiche").first()
        
    if not prestation_fiche:
        messages.error(request, "La prestation 'Fiche' n'est pas configurée.")
        return redirect('enregistrement_patient')
    
    prix_fiche_usd = Decimal(str(prestation_fiche.prix))

    # 2. Calcul du cumul déjà payé
    paiements_existants = Paiement.objects.filter(patient=patient, service='FICHE')
    total_deja_paye_usd = Decimal('0.00')
    
    for p in paiements_existants:
        if p.devise == 'CDF':
            total_deja_paye_usd += p.montant_verse / taux
        else:
            total_deja_paye_usd += p.montant_verse

    reste_a_payer_usd = prix_fiche_usd - total_deja_paye_usd

    if request.method == 'POST':
        montant_saisi = Decimal(request.POST.get('montant', 0))
        devise = request.POST.get('devise')

        montant_test_usd = montant_saisi
        if devise == 'CDF':
            montant_test_usd = montant_saisi / taux

        if montant_test_usd > (reste_a_payer_usd + Decimal('0.01')):
            messages.error(request, f"Le montant dépasse le reste à payer ({reste_a_payer_usd:.2f} USD).")
        elif montant_saisi > 0:
            # Enregistrement du paiement
            Paiement.objects.create(
                patient=patient,
                service='FICHE',
                montant_verse=montant_saisi,
                devise=devise,
                caissier=request.user
            )
            
            # --- NOUVELLE LOGIQUE DE VÉRIFICATION ---
            # On recalcule le total après le nouveau paiement
            nouveau_total_usd = total_deja_paye_usd + montant_test_usd
            
            # Si le total atteint ou dépasse le prix (avec marge d'erreur 0.01)
            if nouveau_total_usd >= (prix_fiche_usd - Decimal('0.01')):
                patient.fiche_payee = True  # Assure-toi que ce champ existe dans ton modèle Patient
                patient.save()
                messages.success(request, f"Paiement terminé. La fiche de {patient.noms} est maintenant validée.")
            else:
                messages.success(request, f"Paiement de {montant_saisi} {devise} enregistré. Reste : {(prix_fiche_usd - nouveau_total_usd):.2f} USD")
            
            return redirect('enregistrement_patient')

    # ... reste du contexte ...
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patient': patient,
        'reste_a_payer': reste_a_payer_usd,
        'reste_a_payer_cdf': reste_a_payer_usd * taux,
        'taux': taux,
        'prix_fiche': prix_fiche_usd,
        'libelle_prestation': prestation_fiche.libelle,
        'fonctionKey' : fonctionKey,
        'deja_paye': patient.fiche_payee # Pour l'utiliser dans le template si besoin
    }
    return render(request, 'back-end/finance/payer_fiche.html', context)

# 21
# ==================================================================================================
# HISTORIQUE DE PAIEMENT
# ==================================================================================================
@login_required
def historique_paiements(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # 1. RÉCUPÉRATION DU TAUX DEPUIS TON MODÈLE ConfigurationHopital
    config = ConfigurationHopital.objects.first()
    # Si la config n'existe pas en DB, on prend 2500 par défaut
    taux = config.taux_usd_en_cdf if config else Decimal('2500.00')
    
    # 2. RÉCUPÉRATION DU PRIX DE LA FICHE (6 USD)
    # On essaie de prendre le prix du service lié au patient
    try:
        cout_total_usd = Decimal(str(patient.service.prix))
    except (AttributeError, ValueError, TypeError):
        # Si le service n'a pas de prix, on cherche la prestation "Fiche" en admin
        from .models import Prestation # Adapte l'import selon ton fichier
        prestation = Prestation.objects.filter(libelle__icontains="Fiche").first()
        cout_total_usd = Decimal(str(prestation.prix)) if prestation else Decimal('0.00')

    # 3. CALCUL PRÉCIS DES PAIEMENTS
    paiements = Paiement.objects.filter(patient=patient).order_by('date_paiement')
    
    cumul_usd = Decimal('0.00')
    historique_detaille = []
    
    for p in paiements:
        # Conversion : Montant / Taux (ex: 10000 / 2500 = 4.00 USD)
        if p.devise == 'CDF':
            montant_equivalent_usd = (p.montant_verse / taux).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            montant_equivalent_usd = p.montant_verse
            
        cumul_usd += montant_equivalent_usd
        
        # Calcul du reste après ce versement précis
        reste_ligne_usd = cout_total_usd - cumul_usd
        
        historique_detaille.append({
            'date': p.date_paiement,
            'service': p.get_service_display(),
            'montant': p.montant_verse,
            'devise': p.devise,
            'caissier': p.caissier.username if p.caissier else "Système",
            'reste_usd': reste_ligne_usd if reste_ligne_usd > 0 else Decimal('0.00'),
            'id': p.id
        })

    # Inverser pour voir le plus récent en haut
    historique_detaille.reverse()

    # Rôles
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # Totaux finaux pour les cartes
    reste_final_usd = max(0, cout_total_usd - cumul_usd)

    context = {
        'patient': patient,
        'paiements_liste': historique_detaille,
        'cout_total_usd': cout_total_usd,
        'total_paye_usd': cumul_usd,
        'reste_a_payer_usd': reste_final_usd,
        'reste_a_payer_cdf': (reste_final_usd * taux).quantize(Decimal('1'), rounding=ROUND_HALF_UP),
        'taux': taux,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/finance/historique.html', context)


# 22
# ==================================================================================================
# IMPRIMER FACTURE
# ==================================================================================================
@login_required
def imprimer_recu_direct(request, paiement_id):
    paiement = get_object_or_404(Paiement, id=paiement_id)
    
    # On ajoute manuellement les 11 heures de décalage
    # pour compenser l'heure système du serveur
    date_reelle = paiement.date_paiement + timedelta(hours=11)

    context = {
        'paiement': paiement,
        'patient': paiement.patient,
        'date_paiement_fix': date_reelle,
    }
    return render(request, 'back-end/finance/ticket_paiement.html', context)

# 23
# ==================================================================================================
# PATIENT LISTE D'ATTENTE TRIAGE
# ==================================================================================================
@login_required
def liste_attente_triage(request):
    # On récupère le taux de 2300 que tu as défini
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2300.00
    
    patients_liste = Patient.objects.all().order_by('-date_creation')
    
    for patient in patients_liste:
        # On filtre les paiements du patient pour le service 'FICHE' uniquement
        paiements = Paiement.objects.filter(patient=patient, service='FICHE')
        
        total_usd = 0
        for p in paiements:
            if p.devise == 'USD':
                total_usd += p.montant_verse
            else:
                # Conversion stricte : montant CDF / 2300
                total_usd += (p.montant_verse / taux)
        
        patient.total_fiche_usd = total_usd
        # Seuil strict de 6.00 USD (soit 13 800 FC)
        patient.a_solde_fiche = total_usd >= 6.00

    # Rôles
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/infirmerie/liste_attente.html', {
        'patients': patients_liste, 
        'taux': taux ,
        'fonctionKey' : fonctionKey
    })



# 24
# ==================================================================================================
# PATIENT SIGNE VITAUX
# ==================================================================================================
@login_required
def saisir_signes(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    today = timezone.now().date()
    
    # On vérifie si un prélèvement non consulté existe déjà pour aujourd'hui
    triage_existant = SigneVital.objects.filter(
        patient=patient,
        date_prelevement__date=today,  
        est_consulte=False
    ).first()

    if request.method == 'POST':
        try:
            if triage_existant:
                # [MODE MISE À JOUR] : Le patient existe déjà, on écrase les anciennes valeurs
                triage_existant.temperature = request.POST.get('temp')
                triage_existant.poids = request.POST.get('poids')
                triage_existant.tension_arterielle = request.POST.get('tension')
                triage_existant.frequence_cardiaque = request.POST.get('pouls')
                triage_existant.frequence_respiratoire = request.POST.get('f_resp')
                triage_existant.saturation_oxygene = request.POST.get('spo2')
                triage_existant.infirmier = request.user  # L'infirmier qui fait la modification
                triage_existant.date_prelevement = timezone.now()  # On actualise l'heure du prélèvement
                triage_existant.save()
                
                messages.success(request, f"Les signes vitaux de {patient.noms} ont été actualisés avec succès.")
            else:
                # [MODE CRÉATION] : Premier prélèvement de la journée pour ce patient
                SigneVital.objects.create(
                    patient=patient,
                    temperature=request.POST.get('temp'),
                    poids=request.POST.get('poids'),
                    tension_arterielle=request.POST.get('tension'),
                    frequence_cardiaque=request.POST.get('pouls'),
                    frequence_respiratoire=request.POST.get('f_resp'),
                    saturation_oxygene=request.POST.get('spo2'),
                    infirmier=request.user,
                    est_consulte=False 
                )
                messages.success(request, f"Signes vitaux de {patient.noms} enregistrés avec succès.")
                
            return redirect('liste_attente_triage')
            
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de l'enregistrement : {str(e)}")

    else:
        # En mode GET : Si le patient a déjà des constantes saisies aujourd'hui
        if triage_existant:
            messages.info(
                request, 
                f"Note : Ce patient a déjà été prélevé aujourd'hui à {triage_existant.date_prelevement.strftime('%H:%M')}. "
                "Modifier les valeurs ci-dessous mettra à jour sa fiche en attente."
            )

    # Gestion des rôles pour l'interface
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/infirmerie/form_triage.html', {
        'patient': patient, 
        'fonctionKey': fonctionKey,
        'triage_existant': triage_existant  # Passe ceci au HTML pour injecter les `value="{{ triage_existant.temperature }}"` dans les inputs
    })
# 25
# ==================================================================================================
# PATIENT LISTE GLOBALE SIGNE VITAUX 
# ==================================================================================================
@login_required
def liste_globale_triage(request):
    # On récupère tous les signes vitaux, mais on ne garde qu'un seul exemplaire par patient
    # On trie par date pour avoir les derniers prélèvements en haut
    historique_global = SigneVital.objects.select_related('patient', 'infirmier').all().order_by('-date_prelevement')

    # Gestion du rôle pour le sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'fonctionKey': fonctionKey,
        'historique': historique_global,
    }
    return render(request, 'back-end/infirmerie/liste_globale_triage.html', context)

# 26
# ==================================================================================================
# PATIENT SIGNE VITAUX  HISTORIQUE
# ==================================================================================================
@login_required
def historique_signes_vitaux(request, patient_id):
    # On récupère le patient spécifique ou erreur 404
    patient = get_object_or_404(Patient, id=patient_id)
    
    # On récupère tout l'historique des prélèvements pour ce patient
    # trié du plus récent au plus ancien
    historique = SigneVital.objects.filter(patient=patient).order_by('-date_prelevement')
    
    # Récupération du rôle pour le sidebar (ton système habituel)
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patient': patient,
        'historique': historique,
        'fonctionKey': fonctionKey,
    }
    return render(request, 'back-end/infirmerie/historique_signes.html', context)


# 27
# ==================================================================================================
# MEDECIN LISTE CONSULTATION VOIR SIGNE VITAUX
# ==================================================================================================
@login_required
def liste_consultation_medecin(request):
    # On affiche uniquement les patients dont les signes vitaux 
    # n'ont pas encore été traités par le médecin
    patients_prets = SigneVital.objects.filter(
        est_consulte=False
    ).select_related('patient', 'infirmier').order_by('date_prelevement')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'fonctionKey': fonctionKey,
        'patients_prets': patients_prets,
    }
    return render(request, 'back-end/medecin/liste_consultation.html', context)

# 28
# ==================================================================================================
# MEDECIN MARQUER CONSULTER POUR N'EST PLUS VOIR DANS LA LISTE
# ==================================================================================================
@login_required
def marquer_consulte(request, sv_id):
    # 1. On récupère le prélèvement spécifique
    signe = get_object_or_404(SigneVital, id=sv_id)
    
    # 2. On marque comme consulté pour qu'il disparaisse DIRECTEMENT de la liste d'attente
    signe.est_consulte = True
    signe.save()
    
    # 3. Redirection vers l'espace de travail du médecin
    return redirect('consultation_medicale', triage_id=sv_id)

# 30
# ==================================================================================================
# MEDECIN   CONSULTATION PATIENT
# ==================================================================================================

@login_required
def consultation_medicale(request, triage_id):
    # 1. Récupération des données de base
    triage = get_object_or_404(SigneVital, id=triage_id)
    
    # On vérifie si une consultation a déjà été enregistrée pour ce triage
    consultation = Consultation.objects.filter(triage=triage).first()

    # [SÉCURITÉ ANTI-DUBLON MODIFIÉE] 
    # On bloque UNIQUEMENT si le triage est marqué consulté ET qu'une consultation existe déjà.
    # Si le médecin vient de cliquer sur le bouton, 'consultation' est None, donc il peut entrer.
    if triage.est_consulte and consultation is not None:
        messages.warning(request, f"Le dossier de consultation pour {triage.patient.noms} a déjà été clôturé.")
        return redirect('liste_consultation_medecin')

    if request.method == 'POST':
        # Double vérification de sécurité au cas où deux utilisateurs soumettent en même temps
        if consultation is not None:
            messages.error(request, "Erreur : Cette consultation a déjà été enregistrée par un autre utilisateur.")
            return redirect('liste_consultation_medecin')

        # Initialisation du formulaire avec les données POST
        form = ConsultationForm(request.POST, instance=consultation)
        
        # Récupération des données manuelles (Tableaux dynamiques)
        examens_ids = request.POST.getlist('examens_ids')
        noms_medocs = request.POST.getlist('nom_medicament')
        posologies = request.POST.getlist('posologie')
        durees = request.POST.getlist('duree')

        # 2. Validation
        if form.is_valid():
            try:
                with transaction.atomic():
                    # On vérifie si une consultation s'est créée entre temps
                    if Consultation.objects.filter(triage=triage).exists():
                        raise Exception("Ce patient a déjà été pris en charge entre-temps.")

                    # A. Sauvegarde de la consultation clinique
                    consultation_obj = form.save(commit=False)
                    consultation_obj.triage = triage
                    consultation_obj.medecin = request.user
                    consultation_obj.save()

                    # B. Gestion des Examens Paracliniques
                    DemandeExamen.objects.filter(consultation=consultation_obj, statut='EN_ATTENTE').delete()
                    for e_id in examens_ids:
                        prestation = get_object_or_404(Prestation, id=e_id)
                        qty_value = request.POST.get(f'qty_{e_id}', 1)
                        
                        DemandeExamen.objects.create(
                            consultation=consultation_obj,
                            prestation=prestation,
                            quantite=qty_value,
                            statut='EN_ATTENTE'
                        )

                    # C. Gestion de l'Ordonnance d'Urgence
                    if any(n.strip() for n in noms_medocs if n):
                        ordonnance, _ = Ordonnance.objects.get_or_create(
                            consultation=consultation_obj,
                            type_ordonnance='URGENCE'
                        )
                        LigneMedicament.objects.filter(ordonnance=ordonnance).delete()
                        
                        for i, nom in enumerate(noms_medocs):
                            if nom and nom.strip():
                                poso = posologies[i] if i < len(posologies) else ""
                                dur = durees[i] if i < len(durees) else ""
                                
                                LigneMedicament.objects.create(
                                    ordonnance=ordonnance,
                                    nom_medicament=nom,
                                    posologie=poso,
                                    duree=dur,
                                    statut='EN_COURS'
                                )

                    # D. Mise à jour définitive du statut du Triage
                    triage.est_consulte = True
                    triage.save()

                messages.success(request, f"Consultation de {triage.patient.noms} enregistrée et clôturée avec succès !")
                return redirect('liste_consultation_medecin')

            except Exception as e:
                messages.error(request, f"Une erreur technique est survenue : {str(e)}")
        else:
            messages.error(request, "Veuillez vérifier les erreurs dans le formulaire clinique.")
    
    else:
        # Mode GET : affichage normal
        form = ConsultationForm(instance=consultation)

    # 3. Préparation du contexte
    examens_disponibles = Prestation.objects.filter(
        categorie__in=['LABO', 'ECHO', 'RADIO']
    ).order_by('categorie', 'libelle')
    
    role = None
    try:
        from .models import Fonction
        role_obj = Fonction.objects.filter(userKey=request.user).first()
        role = role_obj.fonctionKey.roleName if role_obj else None
    except:
        pass
    
    context = {
        'triage': triage,
        'form': form,
        'examens_disponibles': examens_disponibles,
        'consultation': consultation,
        'fonctionKey': role
    }
    return render(request, 'back-end/medecin/consultation_medecin.html', context)





# 30
# ==================================================================================================
# MEDECIN  LISTE DES EXAMENS CONSULTER
# ==================================================================================================
@login_required
def liste_consultations_terminees(request):
    # Optimisation de la requête avec le bon nom de relation : 'examens'
    consultations = Consultation.objects.select_related(
        'triage__patient',      
        'medecin'               
    ).prefetch_related(
        'examens__prestation'  # Utilise 'examens' car related_name='examens'
    ).order_by('-date_creation')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None
    
    context = {
        'consultations': consultations,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/medecin/liste_consultations.html', context)

# 31
# ==================================================================================================
# MEDECIN  DETAILS CONSULTATION 
# ==================================================================================================
@login_required
def detail_consultation(request, pk):
    # On récupère la consultation avec ses relations pour éviter trop de requêtes SQL
    consultation = get_object_or_404(
        Consultation.objects.select_related('triage__patient', 'medecin').prefetch_related('examens__prestation'), 
        pk=pk
    )
    return render(request, 'back-end/medecin/detail_consultation.html', {'c': consultation})


# 32
# ==================================================================================================
# MEDECIN  VOIR LES ORDONNANCES D'URGENCE
# ==================================================================================================
@login_required
def liste_ordonnances_urgence(request):
    query = request.GET.get('q')
    
    # 1. Filtre strict sur le type 'URGENCE' et correction du tri avec 'date_prescrite'
    ordonnances_list = Ordonnance.objects.filter(
        type_ordonnance='URGENCE'
    ).select_related(
        'consultation__triage__patient',
        'consultation__medecin'
    ).prefetch_related(
        'medicaments' # Utilise le nom exact de ton champ ManyToMany ou Related_name ici
    ).order_by('-date_prescrite') # CORRECTION ICI

    # 2. Recherche par nom de patient ou code patient
    if query:
        ordonnances_list = ordonnances_list.filter(
            Q(consultation__triage__patient__noms__icontains=query) |
            Q(consultation__triage__patient__code_patient__icontains=query)
        )

    # 3. Pagination à 10 éléments par page
    paginator = Paginator(ordonnances_list, 10)
    page = request.GET.get('page')
    
    try:
        ordonnances = paginator.page(page)
    except PageNotAnInteger:
        ordonnances = paginator.page(1)
    except EmptyPage:
        ordonnances = paginator.page(paginator.num_pages)

    # 4. Rôle de l'utilisateur pour la sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None
    
    context = {
        'ordonnances': ordonnances,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/medecin/liste_ordonnances_urgence.html', context)

# 33
# ==================================================================================================
# MEDECIN  ORDONNANCE D'URGENCE
# ==================================================================================================
@login_required
def prescrire_ordonnance_urgence_rapide(request, consultation_id):
    if request.method == 'POST':
        consultation = get_object_or_404(Consultation, id=consultation_id)
        observation = request.POST.get('observation')
        medicaments_text = request.POST.get('medicaments_text') # Contenu texte libre ou liste
        
        # 1. Création de l'ordonnance d'urgence
        ordonnance = Ordonnance.objects.create(
            consultation=consultation,
            type_ordonnance='URGENCE',
            observation=f"{observation} | Produits prescrits : {medicaments_text}" if medicaments_text else observation
        )
        
        messages.success(request, f"Ordonnance d'urgence #{ordonnance.id} créée avec succès pour {consultation.triage.patient.noms} !")
        
    # Redirige vers la page d'où vient l'utilisateur
    return redirect(request.META.get('HTTP_REFERER', 'liste_consultations_terminees'))