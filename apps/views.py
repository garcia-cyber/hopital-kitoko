from django.shortcuts import render , redirect , get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth import authenticate , login as auth_login , logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm ,UserChangeForm
from django.contrib import messages
from django.db.models import Q , Sum , DecimalField ,Prefetch , Count
from decimal import Decimal , ROUND_HALF_UP , InvalidOperation
import pytz
from datetime import timedelta , date
from django.db import transaction
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Coalesce , Length


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

    # compte les entreprises
    entreprise = Entreprise.objects.count()



    return render(request , 'back-end/index.html',
                  {
                  'fonctionKey': fonctionKey,
                  'utilisateurs' : utilisateurs ,
                  'total_patients' : total_patients ,
                  'entreprise' : entreprise
                  }
                  )
# 5
# ===========================================================================
# AJOUTER UTILISATEURS
# ===========================================================================
@login_required
def employeAdd(request):
    msg = None
    
    if request.method == 'POST':
        form = EmployeForm(request.POST, request.FILES) # Ajout de request.FILES si le formulaire contient des images/fichiers
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Message de succès
            msg = "Employé enregistré avec succès !"
            
            # Optionnel mais recommandé : Rediriger ou réinitialiser le formulaire pour éviter les doubles soumissions si on rafraîchit la page
            form = EmployeForm() 
    else:
        # Le formulaire vide n'est créé QUE si la méthode est GET
        form = EmployeForm()

    # Vérification de la fonction de l'utilisateur connecté
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'fonctionKey': fonctionKey, 
        'form': form, 
        'msg': msg
    }
    return render(request, 'back-end/employeAdd.html', context)

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
    
    # 1. RÉCUPÉRATION DU TAUX
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else Decimal('2500.00')
    
    # 2. CALCUL DU COÛT DE LA FICHE
    try:
        cout_fiche_usd = Decimal(str(patient.service.prix))
    except (AttributeError, ValueError, TypeError):
        prestation_fiche = Prestation.objects.filter(libelle__icontains="Fiche").first()
        cout_fiche_usd = Decimal(str(prestation_fiche.prix)) if prestation_fiche else Decimal('0.00')

    # 3. CALCUL DU COÛT DE TOUS LES EXAMENS PRESCRITS
    cout_examens_usd = Prestation.objects.filter(
        demandeexamen__consultation__triage__patient=patient
    ).aggregate(total=Sum('prix'))['total'] or Decimal('0.00')
    
    # COÛT TOTAL GLOBAL
    cout_total_usd = cout_fiche_usd + Decimal(str(cout_examens_usd))

    # 4. RÉCUPÉRATION DES VERSEMENTS CHRONOLOGIQUES
    paiements = Paiement.objects.filter(patient=patient).order_by('date_paiement')
    
    historique_detaille = []
    
    # 🛠️ STRATÉGIE CHRONOLOGIQUE DE LA DETTE :
    # On commence la dette à 0. Elle augmente dès qu'un service est facturé/payé.
    cumul_paye_usd = Decimal('0.00')
    
    for p in paiements:
        # Conversion devise
        if p.devise == 'CDF':
            montant_equivalent_usd = (p.montant_verse / taux).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            montant_equivalent_usd = p.montant_verse
            
        cumul_paye_usd += montant_equivalent_usd

        # Déterminer la cible du coût à cet instant précis pour éviter le saut à 85$
        if p.service == 'FICHE':
            # Si c'est la fiche, le reste ne doit pas inclure les examens pas encore payés à ce moment là
            reste_ligne_usd = cout_fiche_usd - montant_equivalent_usd
        else:
            # Si c'est un examen, on calcule par rapport au reste global
            reste_ligne_usd = cout_total_usd - cumul_paye_usd
        
        # Récupération des détails des examens payés
        examens_associes = []
        if p.consultation and p.service in ['LABO', 'RADIO', 'ECHOGRAPHIE']:
            examens_payes = p.consultation.examens.filter(statut__in=['EN_COURS', 'TERMINE']).select_related('prestation')
            for exam in examens_payes:
                examens_associes.append({
                    'libelle': exam.prestation.libelle,
                    'prix': exam.prestation.prix
                })
        
        historique_detaille.append({
            'date': p.date_paiement,
            'service': p.get_service_display(),
            'montant': p.montant_verse,
            'devise': p.devise,
            'caissier': p.caissier.username if p.caissier else "Système",
            'reste_usd': max(Decimal('0.00'), reste_ligne_usd),
            'examens': examens_associes,
            'id': p.id
        })

    # Inverser pour l'affichage du plus récent au plus ancien
    historique_detaille.reverse()

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # Totaux finaux pour les cartes du haut
    reste_final_usd = max(Decimal('0.00'), cout_total_usd - cumul_paye_usd)

    context = {
        'patient': patient,
        'paiements_liste': historique_detaille,
        'cout_total_usd': cout_total_usd,
        'total_paye_usd': cumul_paye_usd,
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
    
    # 🛠️ CORRECTION 1 : Suppression des 11 heures de décalage artificiel
    # Django gère déjà le fuseau horaire via les filtres de template ou l'heure locale
    date_reelle = paiement.date_paiement 

    # 🛠️ CORRECTION 2 : Traçabilité des examens spécifiques à ce paiement
    examens_associes = []
    if paiement.consultation and paiement.service in ['LABO', 'RADIO', 'ECHOGRAPHIE']:
        # On extrait les examens payés (statut libéré) liés à cette consultation précise
        examens_payes = paiement.consultation.examens.filter(
            statut__in=['EN_COURS', 'TERMINE']
        ).select_related('prestation')
        
        for exam in examens_payes:
            examens_associes.append({
                'libelle': exam.prestation.libelle,
                'prix': exam.prestation.prix
            })

    context = {
        'paiement': paiement,
        'patient': paiement.patient,
        'date_paiement_fix': date_reelle,
        'examens_ticket': examens_associes,  # Envoyé au template du ticket
    }
    return render(request, 'back-end/finance/ticket_paiement.html', context)
# 23
# ==================================================================================================
# PATIENT LISTE D'ATTENTE TRIAGE
# ==================================================================================================
@login_required
def liste_attente_triage(request):
    # On récupère le taux
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2300.00
    
    patients_liste = Patient.objects.all().order_by('-date_creation')
    
    for patient in patients_liste:
        # 1. Vérification du solde Fiche (Logique maintenue)
        paiements = Paiement.objects.filter(patient=patient, service='FICHE')
        
        total_usd = 0
        for p in paiements:
            if p.devise == 'USD':
                total_usd += p.montant_verse
            else:
                # Conversion stricte : montant CDF / taux
                total_usd += (p.montant_verse / taux)
        
        patient.total_fiche_usd = total_usd
        # Seuil strict de 6.00 USD
        patient.a_solde_fiche = total_usd >= 6.00
        
        # 2. Vérification signes vitaux (Ajouté sans supprimer le reste)
        patient.a_signes_vitaux_deja_pris = SigneVital.objects.filter(patient=patient).exists()

    # Rôles
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/infirmerie/liste_attente.html', {
        'patients': patients_liste, 
        'taux': taux,
        'fonctionKey': fonctionKey
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

# 34
# ==================================================================================================
# RECEPTIONNISTE PAIEMENT DES EXAM
# ==================================================================================================
@login_required
def encaisser_examens_prescrits(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # On récupère TOUS les examens qui attendent encore un paiement
    examens_en_attente = consultation.examens.filter(statut='EN_ATTENTE')

    # Si aucun examen n'est en attente, on dégage la consultation
    if not examens_en_attente.exists():
        messages.warning(request, "Tous les examens de cette consultation ont déjà été payés.")
        return redirect('liste_attente_caisse')

    if request.method == 'POST':
        # 1. Récupérer les IDs des examens cochés par le caissier dans le template
        examen_ids_payes = request.POST.getlist('examens_choisis')

        if not examen_ids_payes:
            messages.error(request, "Veuillez sélectionner au moins un examen à encaisser.")
            return redirect('encaisser_examens_prescrits', consultation_id=consultation.id)

        # 2. Filtrer sécurisé : on ne prend que les examens cochés ET qui appartiennent bien à cette consultation
        examens_a_regler = examens_en_attente.filter(id__in=examen_ids_payes)

        if examens_a_regler.exists():
            # 3. Calculer dynamiquement le montant des examens sélectionnés
            total_selection = examens_a_regler.aggregate(
                total=Sum('prestation__prix')
            )['total'] or 0

            # Calcul de la dette restante avant validation pour l'affichage du message
            total_global_avant = examens_en_attente.aggregate(
                total=Sum('prestation__prix')
            )['total'] or 0
            
            dette_restante = total_global_avant - total_selection

            # 4. Détection automatique du service majeur selon la sélection réelle
            contient_radio = examens_a_regler.filter(prestation__libelle__icontains="radio").exists()
            contient_echo = examens_a_regler.filter(prestation__libelle__icontains="écho").exists()
            
            if contient_radio:
                service_choisi = 'RADIO'
            elif contient_echo:
                service_choisi = 'ECHOGRAPHIE'
            else:
                service_choisi = 'LABO'

            # 5. Création de l'entrée de paiement (sans l'argument invalide 'dette')
            paiement = Paiement.objects.create(
                patient=consultation.triage.patient,
                consultation=consultation,
                service=service_choisi,
                montant_verse=total_selection,
                devise='USD',
                caissier=request.user,
                date_paiement=timezone.now()
            )

            # 6. Libération EXCLUSIVE des examens payés (Le statut passe de 'EN_ATTENTE' à 'EN_COURS')
            # C'est ce changement de statut qui fait que l'examen n'est plus compté dans la dette au rechargement
            for examen in examens_a_regler:
                examen.statut = 'EN_COURS'
                examen.save()

            # Message flash personnalisé s'il reste des examens non payés
            if dette_restante > 0:
                messages.warning(
                    request, 
                    f"Encaissé : {total_selection} USD. Il reste des examens non réglés d'une valeur de {dette_restante} USD "
                    f"pour le patient {consultation.triage.patient.noms}."
                )
                return redirect('encaisser_examens_prescrits', consultation_id=consultation.id)
            
            else:
                messages.success(
                    request, 
                    f"Encaissé avec succès : {total_selection} USD. Tous les examens ont été payés !"
                )
                return redirect('liste_attente_caisse')
                
        else:
            messages.error(request, "Les examens sélectionnés sont invalides ou déjà réglés.")
            return redirect('liste_attente_caisse')

    # Pour l'affichage GET initial : calcul du reste total à payer globalement
    total_global_restant = examens_en_attente.aggregate(total=Sum('prestation__prix'))['total'] or 0

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'consultation': consultation,
        'examens': examens_en_attente,
        'total_a_payer': total_global_restant,
        'fonctionKey': fonctionKey 
    }
    return render(request, 'back-end/caisse/encaisser_examens.html', context)
# 35
# ==================================================================================================
# RECEPTIONNISTE PAIEMENT DES EXAM
# ==================================================================================================
@login_required
def liste_attente_caisse(request):
    # 1. On récupère UNIQUEMENT les consultations qui possèdent encore 
    # au moins un examen avec le statut 'EN_ATTENTE'.
    # Pas besoin d'exclude() sur la table Paiement, la condition 'EN_ATTENTE' suffit !
    consultations_a_payer = Consultation.objects.filter(
        examens__statut='EN_ATTENTE'
    ).distinct()

    # 2. Gestion de la barre de recherche (Inchangée et fonctionnelle)
    query = request.GET.get('q')
    if query:
        consultations_a_payer = consultations_a_payer.filter(
            Q(triage__patient__noms__icontains=query) |
            Q(triage__patient__code_patient__icontains=query) |
            Q(medecin__username__icontains=query)
        ).distinct()

    # 3. Tri par date décroissante
    consultations_a_payer = consultations_a_payer.order_by('-date_creation')

    # 4. Récupération du rôle
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/caisse/liste_attente.html', {
        'consultations': consultations_a_payer,
        'fonctionKey': fonctionKey
    })

# 36
# ==================================================================================================
# LISTE DES EXAMENS A FAIRE 
# ==================================================================================================
@login_required
def liste_examens_techniques(request):
    # 1. Vérification du rôle de l'utilisateur connecté via ton modèle Fonction
    role_user = Fonction.objects.filter(userKey=request.user).first()
    
    if not role_user or not role_user.fonctionKey:
        messages.error(request, "Accès refusé : Aucun rôle ne vous est attribué.")
        return redirect('dashboard')

    nom_role = role_user.fonctionKey.roleName.lower()
    fonctionKey = role_user.fonctionKey.roleName

    # 2. SÉCURITÉ COMPTABLE & TECHNIQUE : 
    # On cible les services concernés
    paiements_techniques = Paiement.objects.filter(
        consultation__isnull=False,
        service__in=['LABO', 'RADIO', 'ECHOGRAPHIE']
    ).select_related('consultation', 'patient', 'consultation__triage')

    examens_presents = False
    historique_technique = []

    # 3. CLOISONNEMENT STRICT PAR PROFIL ET VÉRIFICATION DES STATUTS
    for p in paiements_techniques:
        # ÉVOLUTION : On prend 'EN_COURS' (à faire) ET 'TERMINE' (déjà fait) pour gérer le blocage
        examens_payes = p.consultation.examens.filter(
            statut__in=['EN_COURS', 'TERMINE']
        ).select_related('prestation')
        
        examens_filtrés_pour_role = []
        for exam in examens_payes:
            cat = exam.prestation.categorie
            
            # Déterminer si l'examen est déjà traité (ex: Goutte épaisse déjà validée)
            deja_consulte = (exam.statut == 'TERMINE')

            # Flag pour savoir si la catégorie correspond au rôle
            correspond_au_role = False
            if ('labo' in nom_role or 'laborantin' in nom_role) and cat == 'LABO':
                correspond_au_role = True
            elif ('echo' in nom_role or 'echographe' in nom_role) and cat == 'ECHO':
                correspond_au_role = True
            elif ('radio' in nom_role or 'radiologue' in nom_role) and cat == 'RADIO':
                correspond_au_role = True

            # Si l'examen correspond au service de l'utilisateur, on l'ajoute avec son état
            if correspond_au_role:
                examens_filtrés_pour_role.append({
                    'id_examen': exam.id, # Utile pour tes futurs liens/formulaires
                    'libelle': exam.prestation.libelle,
                    'date': p.date_paiement,
                    'est_deja_fait': deja_consulte  # Notre indicateur pour le template
                })

        if examens_filtrés_pour_role:
            examens_presents = True
            historique_technique.append({
                'id_paiement': p.id,
                'consultation': p.consultation,
                'patient': p.patient,
                'triage': p.consultation.triage if hasattr(p.consultation, 'triage') else None,
                'examens': examens_filtrés_pour_role,
                'medecin': p.consultation.medecin.username if p.consultation.medecin else "Généraliste"
            })

    # Tri du plus récent au plus ancien basé sur les paiements
    historique_technique.reverse()

    # Définition du titre de la page selon le rôle
    if 'labo' in nom_role or 'laborantin' in nom_role:
        titre_page = "Laboratoire - Analyses Payées"
    elif 'echo' in nom_role or 'echographe' in nom_role:
        titre_page = "Échographie - Examens Payés"
    else:
        titre_page = "Radiologie - Examens Payés"

    context = {
        'historique_technique': historique_technique,
        'examens_presents': examens_presents,
        'titre_page': titre_page,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/technique/liste_examens_payes.html', context)


# 37
# ==================================================================================================
# 
# ==================================================================================================
@login_required
def saisir_resultats_examens(request, paiement_id):
    # 1. Vérification du rôle du technicien
    role_user = Fonction.objects.filter(userKey=request.user).first()
    if not role_user or not role_user.fonctionKey:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    nom_role = role_user.fonctionKey.roleName.lower()
    fonctionKey = role_user.fonctionKey.roleName

    # 2. Récupération du paiement et de la consultation associée
    paiement = get_object_or_404(Paiement, id=paiement_id)
    consultation = paiement.consultation

    if not consultation:
        messages.error(request, "Aucune consultation associée à ce paiement.")
        return redirect('liste_examens_techniques')

    # 3. Extraction et filtrage des examens 'EN_COURS' pour ce rôle précis
    # L'utilisation de select_related('prestation') est cruciale ici pour récupérer 'valeur_normale' sans refaire de requêtes SQL
    examens_payes = consultation.examens.filter(statut='EN_COURS').select_related('prestation')
    
    examens_a_saisir = []
    for exam in examens_payes:
        cat = exam.prestation.categorie
        if ('labo' in nom_role or 'laborantin' in nom_role) and cat == 'LABO':
            examens_a_saisir.append(exam)
        elif ('echo' in nom_role or 'echographe' in nom_role) and cat == 'ECHO':
            examens_a_saisir.append(exam)
        elif ('radio' in nom_role or 'radiologue' in nom_role) and cat == 'RADIO':
            examens_a_saisir.append(exam)

    # Sécurité : Si l'accès est forcé par URL alors que tout est déjà traité ou hors spécialité
    if not examens_a_saisir:
        messages.error(request, "Aucun examen en attente de saisie pour votre spécialité.")
        return redirect('liste_examens_techniques')

    # 4. Traitement de la soumission du formulaire (POST)
    if request.method == 'POST':
        examens_traites_count = 0
        
        for exam in examens_a_saisir:
            cle_resultat = f"resultat_{exam.id}"
            texte_resultat = request.POST.get(cle_resultat, "").strip()
            
            if texte_resultat:
                exam.resultat = texte_resultat
                exam.statut = 'TERMINE'  # Passage au statut finalisé
                exam.technicien = request.user  # Traçabilité du technicien
                exam.save()
                examens_traites_count += 1
                
        if examens_traites_count > 0:
            messages.success(request, f"Les résultats de ({examens_traites_count}) examen(s) pour {paiement.patient.noms} ont été enregistrés.")
        else:
            messages.warning(request, "Aucun résultat n'a été saisi.")
            
        return redirect('liste_examens_techniques')

    context = {
        'paiement': paiement,
        'patient': paiement.patient,
        'consultation': consultation,
        'examens_a_saisir': examens_a_saisir,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/technique/saisir_resultats.html', context)

# 38
# ==================================================================================================
# 
# ==================================================================================================
@login_required
def dossier_resultats_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # 1. Récupération de toutes les consultations du patient (de la plus récente à la plus ancienne)
    consultations = Consultation.objects.filter(triage__patient=patient).select_related('medecin').order_by('-date_creation')
    
    historique_consultations_examens = []
    
    for condultation in consultations:
        # 2. Récupération de TOUS les examens liés à CETTE consultation spécifique
        tous_les_examens = condultation.examens.select_related('prestation').all()
        
        # On sépare les examens par catégorie pour un affichage structuré dans le template
        examens_labo = []
        examens_radio = []
        examens_echo = []
        
        for exam in tous_les_examens:
            cat = exam.prestation.categorie
            if cat == 'LABO':
                examens_labo.append(exam)
            elif cat == 'RADIO':
                examens_radio.append(exam)
            elif cat == 'ECHO':
                examens_echo.append(exam)
        
        # On calcule le niveau d'avancement des examens pour cette consultation
        total_examens = tous_les_examens.count()
        examens_termines = tous_les_examens.filter(statut='TERMINE').count()
        
        # Statut global de la fiche d'examen pour le médecin
        if total_examens == 0:
            statut_global = "Aucun examen prescrit"
            classe_badge = "badge-secondary"
        elif examens_termines == total_examens:
            statut_global = "Complet (Tous les résultats sont disponibles)"
            classe_badge = "badge-success"
        elif examens_termines > 0:
            statut_global = f"Incomplet ({examens_termines}/{total_examens} disponible(s))"
            classe_badge = "badge-warning"
        else:
            statut_global = "En attente de réalisation / de paiement"
            classe_badge = "badge-danger"

        # On rassemble les informations de la consultation et ses examens cloisonnés
        historique_consultations_examens.append({
            'consultation': condultation,
            'statut_global': statut_global,
            'classe_badge': classe_badge,
            'labo': examens_labo,
            'radio': examens_radio,
            'echo': examens_echo,
            'a_des_examens': total_examens > 0
        })

    # Récupération du rôle pour la sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patient': patient,
        'historique': historique_consultations_examens,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/medecin/dossier_resultats.html', context)


# 39
# ==================================================================================================
# 
# ==================================================================================================

@login_required
def uniquement_resultats_examens(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Récupérer toutes les consultations du patient
    consultations = Consultation.objects.filter(triage__patient=patient).order_by('-date_creation')
    
    historique_resultats = []
    
    for consult in consultations:
        # On prend UNIQUEMENT les examens terminés (avec un résultat saisi)
        examens_termines = consult.examens.filter(statut='TERMINE').select_related('prestation')
        
        if examens_termines.exists():
            historique_resultats.append({
                'consultation': consult,
                'examens': examens_termines
            })
            
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'patient': patient,
        'historique_resultats': historique_resultats,
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/medecin/resultats_bruts.html', context)

# 40
# ==================================================================================================
#  FINANCE DASHBOARD
# ==================================================================================================
@login_required
def dashboard_finance(request):
    # --- GESTION DES DATES --- 
    maintenant = timezone.now()
    
    # Aujourd'hui à minuit (00:00:00)
    debut_aujourdhui = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Début de la semaine (7 jours glissants)
    debut_semaine = debut_aujourdhui - timedelta(days=7)
    
    # Début du mois (Le 1er du mois en cours à 00:00:00)
    debut_mois = debut_aujourdhui.replace(day=1)

    # --- 1. CALCUL DES ENTRÉES GLOBALES (PAIEMENTS - TOUT HISTORIQUE) ---
    total_usd = Paiement.objects.filter(devise='USD').aggregate(total=Sum('montant_verse'))['total'] or 0.00
    total_cdf = Paiement.objects.filter(devise='CDF').aggregate(total=Sum('montant_verse'))['total'] or 0.00

    # --- 2. CALCUL DES SORTIES GLOBALES (DÉPENSES - TOUT HISTORIQUE) ---
    depense_totale_usd = Depense.objects.filter(devise='USD').aggregate(total=Sum('montant'))['total'] or 0.00
    depense_totale_cdf = Depense.objects.filter(devise='CDF').aggregate(total=Sum('montant'))['total'] or 0.00

    # --- 3. CALCUL DU SOLDE RESTANT REEL EN CAISSE ---
    restant_usd = float(total_usd) - float(depense_totale_usd)
    restant_cdf = float(total_cdf) - float(depense_totale_cdf)

    # --- 4. STATISTIQUES DES ENTRÉES PAR PÉRIODES (USD et CDF) ---
    # Aujourd'hui
    recette_aujourdhui_usd = Paiement.objects.filter(date_paiement__gte=debut_aujourdhui, devise='USD').aggregate(total=Sum('montant_verse'))['total'] or 0.00
    recette_aujourdhui_cdf = Paiement.objects.filter(date_paiement__gte=debut_aujourdhui, devise='CDF').aggregate(total=Sum('montant_verse'))['total'] or 0.00

    # Cette Semaine
    recette_semaine_usd = Paiement.objects.filter(date_paiement__gte=debut_semaine, devise='USD').aggregate(total=Sum('montant_verse'))['total'] or 0.00
    recette_semaine_cdf = Paiement.objects.filter(date_paiement__gte=debut_semaine, devise='CDF').aggregate(total=Sum('montant_verse'))['total'] or 0.00

    # Ce Mois
    recette_mois_usd = Paiement.objects.filter(date_paiement__gte=debut_mois, devise='USD').aggregate(total=Sum('montant_verse'))['total'] or 0.00
    recette_mois_cdf = Paiement.objects.filter(date_paiement__gte=debut_mois, devise='CDF').aggregate(total=Sum('montant_verse'))['total'] or 0.00

    # --- 5. CALCUL DES ENTRÉES PAR SERVICE ET PAR DEVISE (TOUT HISTORIQUE) ---
    services_stats = []
    for code, nom_service in Paiement.SERVICES:
        usd_service = Paiement.objects.filter(service=code, devise='USD').aggregate(total=Sum('montant_verse'))['total'] or 0.00
        cdf_service = Paiement.objects.filter(service=code, devise='CDF').aggregate(total=Sum('montant_verse'))['total'] or 0.00
        
        services_stats.append({
            'nom': nom_service,
            'usd': usd_service,
            'cdf': cdf_service
        })

    # --- 6. LISTE DES PAIEMENTS COMPLETS ---
    tous_les_paiements = Paiement.objects.select_related('patient', 'caissier').order_by('-date_paiement')

    # Extraction du rôle pour la sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # --- 7. ENVOI AU TEMPLATE ---
    context = {
        # Entrées globales (Historique total des paiements reçus)
        'total_usd': total_usd,
        'total_cdf': total_cdf,
        
        # Sorties globales (Historique total des dépenses effectuées)
        'depense_totale_usd': depense_totale_usd,
        'depense_totale_cdf': depense_totale_cdf,
        
        # Net physique restant dans le coffre (Entrées - Sorties)
        'restant_usd': restant_usd,
        'restant_cdf': restant_cdf,
        
        # Stats temporelles des entrées : USD
        'aujourdhui_usd': recette_aujourdhui_usd,
        'semaine_usd': recette_semaine_usd,
        'mois_usd': recette_mois_usd,
        
        # Stats temporelles des entrées : CDF
        'aujourdhui_cdf': recette_aujourdhui_cdf,
        'semaine_cdf': recette_semaine_cdf,
        'mois_cdf': recette_mois_cdf,
        
        # Tables et meta
        'services_stats': services_stats,
        'paiements': tous_les_paiements,
        'fonctionKey': fonctionKey,
        'titre_page': "Journal de Caisse & Finances - Moyanoli"
    }
    return render(request, 'back-end/finance/dashboard_finance.html', context)

# ==================================================================================================
# #41 : FINANCE GESTION DE DETTE 
# ==================================================================================================
@login_required
def creer_depense(request):
    # Extraction du rôle pour la sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    if request.method == 'POST':
        form = DepenseForm(request.POST)
        if form.is_valid():
            # 1. On crée l'objet en mémoire sans le sauvegarder immédiatement en BDD
            depense = form.save(commit=False)
            # 2. On lui attribue automatiquement l'utilisateur connecté comme auteur
            depense.auteur = request.user
            
            # --- VÉRIFICATION STRICTE DU SOLDE DISPONIBLE ---
            devise_saisie = depense.devise  # USD ou CDF
            
            # On force tout en float pour sécuriser les calculs mathématiques
            montant_demande_float = float(depense.montant)

            # Calcule toutes les entrées (Paiements) pour cette devise
            res_entrees = Paiement.objects.filter(devise=devise_saisie).aggregate(
                total=Coalesce(Sum('montant_verse'), 0, output_field=DecimalField())
            )['total']
            
            # Calcule toutes les sorties (Dépenses) déjà validées pour cette devise
            res_sorties = Depense.objects.filter(devise=devise_saisie).aggregate(
                total=Coalesce(Sum('montant'), 0, output_field=DecimalField())
            )['total']

            # Conversion mathématique brute et sécurisée en float
            total_entrees_float = float(res_entrees) if res_entrees else 0.0
            total_sorties_float = float(res_sorties) if res_sorties else 0.0

            # Calcul du solde en float (Plus aucun risque de conflit)
            solde_disponible_float = total_entrees_float - total_sorties_float

            # Blocage manuel si la somme demandée est supérieure à la caisse
            if montant_demande_float > solde_disponible_float:
                form.add_error(None, f"Opération refusée. Solde de caisse insuffisant en {devise_saisie}. Disponible : {solde_disponible_float:.2f} {devise_saisie}. Montant demandé : {montant_demande_float:.2f} {devise_saisie}.")
            else:
                try:
                    # 3. On force l'exécution du clean() du modèle au cas où d'autres validations existent
                    depense.full_clean()
                    depense.save()
                    
                    # Message de succès et redirection vers la bonne vue de journal
                    messages.success(request, "La dépense a été enregistrée avec succès !")
                    return redirect('dashboard_finance_depense')
                    
                except ValidationError as e:
                    # 4. Si une autre validation du modèle échoue, on récupère l'erreur pour l'afficher
                    if hasattr(e, 'message_dict'):
                        for field, errors in e.message_dict.items():
                            for error in errors:
                                form.add_error(None, error)
                    else:
                        for error in e.messages:
                            form.add_error(None, error)
    else:
        form = DepenseForm()

    context = {
        'form': form,
        'titre_page': "Enregistrer une Sortie de Caisse",
        'fonctionKey': fonctionKey,
    }
    return render(request, 'back-end/finance/creer_depense.html', context)


# ==================================================================================================
# 42 : FINANCE GESTION DE DETTE  JOURNAL
# ==================================================================================================
@login_required
def dashboard_finance_depense(request):
    """
    Tableau de bord financier : Journal des entrées,
    statistiques temporelles et bilan global du coffre (USD / CDF).
    """
    # 1. Gestion du rôle pour la sidebar Moyanoli
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # 2. Filtrage temporel (Aujourd'hui, Cette semaine, Ce mois)
    maintenant = timezone.now()
    debut_aujourdhui = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    debut_semaine = debut_aujourdhui - timezone.timedelta(days=maintenant.weekday())
    debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # --- ENTRÉES (PAIEMENTS) ---
    paiements_tous = Paiement.objects.all().order_by('-date_paiement')

    # Utilisation de Decimal('0.00') et output_field pour éviter le mélange de types
    zero_decimal = Decimal('0.00')

    # Statistiques temporelles des entrées
    recettes_stats = Paiement.objects.aggregate(
        auj_usd=Coalesce(Sum('montant_verse', filter=Q(date_paiement__gte=debut_aujourdhui, devise='USD')), zero_decimal, output_field=DecimalField()),
        auj_cdf=Coalesce(Sum('montant_verse', filter=Q(date_paiement__gte=debut_aujourdhui, devise='CDF')), zero_decimal, output_field=DecimalField()),
        sem_usd=Coalesce(Sum('montant_verse', filter=Q(date_paiement__gte=debut_semaine, devise='USD')), zero_decimal, output_field=DecimalField()),
        sem_cdf=Coalesce(Sum('montant_verse', filter=Q(date_paiement__gte=debut_semaine, devise='CDF')), zero_decimal, output_field=DecimalField()),
        mois_usd=Coalesce(Sum('montant_verse', filter=Q(date_paiement__gte=debut_mois, devise='USD')), zero_decimal, output_field=DecimalField()),
        mois_cdf=Coalesce(Sum('montant_verse', filter=Q(date_paiement__gte=debut_mois, devise='CDF')), zero_decimal, output_field=DecimalField()),
    )

    # Totaux globaux des entrées
    total_entrees = Paiement.objects.aggregate(
        usd=Coalesce(Sum('montant_verse', filter=Q(devise='USD')), zero_decimal, output_field=DecimalField()),
        cdf=Coalesce(Sum('montant_verse', filter=Q(devise='CDF')), zero_decimal, output_field=DecimalField())
    )

    # --- SORTIES (DÉPENSES) ---
    total_depenses = Depense.objects.aggregate(
        usd=Coalesce(Sum('montant', filter=Q(devise='USD')), zero_decimal, output_field=DecimalField()),
        cdf=Coalesce(Sum('montant', filter=Q(devise='CDF')), zero_decimal, output_field=DecimalField())
    )

    # --- CALCUL DU SOLDE NET EN COFFRE ---
    restant_usd = total_entrees['usd'] - total_depenses['usd']
    restant_cdf = total_entrees['cdf'] - total_depenses['cdf']

    # --- VENTILATION PAR SERVICE ---
    services_liste = ['FICHE', 'LABO', 'ECHOGRAPHIE', 'RADIO']
    services_stats = []
    for s in services_liste:
        s_usd = Paiement.objects.filter(service=s, devise='USD').aggregate(t=Coalesce(Sum('montant_verse'), zero_decimal, output_field=DecimalField()))['t']
        s_cdf = Paiement.objects.filter(service=s, devise='CDF').aggregate(t=Coalesce(Sum('montant_verse'), zero_decimal, output_field=DecimalField()))['t']
        services_stats.append({'nom': s, 'usd': s_usd, 'cdf': s_cdf})

    context = {
        'titre_page': "Journal Général de Caisse",
        'fonctionKey': fonctionKey,
        'paiements': paiements_tous,
        
        # Variables Recettes Temporelles
        'aujourdhui_usd': recettes_stats['auj_usd'],
        'aujourdhui_cdf': recettes_stats['auj_cdf'],
        'semaine_usd': recettes_stats['sem_usd'],
        'semaine_cdf': recettes_stats['sem_cdf'],
        'mois_usd': recettes_stats['mois_usd'],
        'mois_cdf': recettes_stats['mois_cdf'],
        
        # Variables Bilan Coffre-Fort
        'total_usd': total_entrees['usd'],
        'total_cdf': total_entrees['cdf'],
        'depense_totale_usd': total_depenses['usd'],
        'depense_totale_cdf': total_depenses['cdf'],
        'restant_usd': restant_usd,
        'restant_cdf': restant_cdf,
        
        'services_stats': services_stats,
    }
    return render(request, 'back-end/finance/journal_caisse.html', context)

# ==================================================================================================
# 43 : RESULTAT DU LABO RADIO ET ECHO PAR LE MEDECIN
# ==================================================================================================
@login_required
def liste_attente_ordonnance_view(request):
    # 1. Gestion de l'enregistrement de l'ordonnance (POST)
    if request.method == 'POST' and request.POST.get('action') == 'enregistrer_ordonnance':
        consultation_id = request.POST.get('consultation_id')
        diagnostic = request.POST.get('diagnostic_final')
        contenu = request.POST.get('contenu_ordonnance')
        type_ord = request.POST.get('type_ordonnance')
        
        noms = request.POST.getlist('nom_medicament[]')
        posologies = request.POST.getlist('posologie[]')
        durees = request.POST.getlist('duree[]')
        
        consultation = Consultation.objects.filter(id=consultation_id).first()
        
        if consultation:
            try:
                with transaction.atomic():
                    consultation.diagnostic_final = diagnostic
                    consultation.save()
                    
                    ordonnance = Ordonnance.objects.create(
                        consultation=consultation,
                        observation=contenu,
                        type_ordonnance=type_ord
                    )
                    
                    for nom, pos, dur in zip(noms, posologies, durees):
                        if nom.strip():
                            Medicament.objects.create(
                                ordonnance=ordonnance,
                                nom=nom,
                                posologie=pos,
                                duree=dur
                            )
                messages.success(request, "Ordonnance enregistrée avec succès.")
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        return redirect(request.path_info)

    # 2. Récupération des données pour le template (GET)
    # Optimisation avec prefetch_related pour éviter les requêtes SQL en boucle
    consultations_en_attente = Consultation.objects.filter(
        examens__statut='TERMINE'
    ).prefetch_related(
        'examens', 
        'ordonnance_set'
    ).distinct()

    # 3. Gestion des rôles utilisateur
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None 
    
    return render(request, 'back-end/medecin/liste_attente.html', {
        'consultations_en_attente': consultations_en_attente, 
        'fonctionKey': fonctionKey 
    })

 
# ==================================================================================================
# 44 : RESULTAT HISTORIQUE SOIT LABO , RADIO OU ECHO
# ==================================================================================================
@login_required
def historique_examens_view(request):
    """
    Vue pour afficher l'historique de tous les examens terminés dans Moyanoli avec pagination.
    """
    # 1. Récupération et optimisation du QuerySet de base
    examens_liste = DemandeExamen.objects.filter(
        statut='TERMINE'
    ).select_related(
        'consultation__triage__patient',  # Accès direct aux infos du patient
        'prestation',                     # Accès au prix et libellé de l'examen
        'technicien'                      # Accès à l'utilisateur qui a fait l'examen
    ).prefetch_related(
        'technicien__user_fonction__fonctionKey'  # Récupère la fonction et le rôle associé
    ).order_by('-date_realisation')

    # 2. Configuration de la pagination (ex: 10 examens par page)
    elements_par_page = 10
    paginator = Paginator(examens_liste, elements_par_page)
    
    # 3. Récupération du numéro de la page actuelle depuis l'URL (?page=...)
    page_number = request.GET.get('page')
    
    try:
        historique_examens = paginator.get_page(page_number)
    except PageNotAnInteger:
        # Si le paramètre page n'est pas un entier, on renvoie la première page
        historique_examens = paginator.page(1)
    except EmptyPage:
        # Si la page est hors limites, on renvoie la dernière page de résultats
        historique_examens = paginator.page(paginator.num_pages)

    # 4. Gestion des rôles utilisateur
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    context = {
        'historique_examens': historique_examens,  # Cet objet contient maintenant les méthodes de pagination (.has_next, etc.)
        'fonctionKey': fonctionKey
    }
    
    return render(request, 'back-end/examens/historique.html', context)

# ==================================================================================================
# 45 : GESTION HOPITALISATION
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# VUE : Vue principale agissant comme tableau de bord pour piloter les infrastructures physiques.
# FONCTION : Récupère toutes les chambres (avec jointures optimisées), calcule les statistiques 
#            d'occupation globales en temps réel et génère l'affichage du plan des salles.
# --------------------------------------------------------------------------------------------------
@login_required
def dashboard_chambres(request):
    """ Affichage global de la situation des chambres, prix et lits """
    
    # 1. Récupération des chambres avec jointures optimisées
    chambres = Chambre.objects.all().select_related('type_chambre').prefetch_related('lits')

    # 2. Gestion des rôles utilisateur
    role = Fonction.objects.filter(userKey=request.user).select_related('fonctionKey').first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # 3. Statistiques globales en UNE SEULE requête SQL (Agrégation)
    # Cela évite de solliciter la base de données plusieurs fois inutilement.
    stats = Lit.objects.aggregate(
        total_lits=Count('id', filter=Q(est_actif=True)),
        lits_occupes=Count('id', filter=Q(est_occupe=True, est_actif=True)),
        lits_disponibles=Count('id', filter=Q(est_occupe=False, est_actif=True))
    )

    context = {
        'fonctionKey': fonctionKey,
        'chambres': chambres,
        'total_chambres': chambres.filter(est_active=True).count(),
        'total_lits': stats['total_lits'],
        'lits_occupes': stats['lits_occupes'],
        'lits_disponibles': stats['lits_disponibles'],
    }
    
    return render(request, 'back-end/hospitalisation/dashboard_chambres.html', context)


# --------------------------------------------------------------------------------------------------
# VUE : Première étape de la configuration de l'infrastructure de soins.
# FONCTION : Permet d'enregistrer une nouvelle catégorie de tarification ou de destination médicale 
#            (ex: VIP, Soins Intensifs, Pédiatrie) avant de pouvoir y affecter des locaux.
# --------------------------------------------------------------------------------------------------
@login_required
def ajouter_type_chambre(request):
    """ Étape 1 : Enregistrer une catégorie (VIP, Commune, etc.) """
    if request.method == 'POST':
        form = TypeChambreForm(request.POST)
        if form.is_valid():
            type_chambre = form.save()
            messages.success(request, f"Le type de chambre '{type_chambre.libelle}' a été enregistré.")
            # Redirection logique et fluide vers l'étape 2 (Ajout d'une pièce physique)
            return redirect('ajouter_chambre') 
    else:
        form = TypeChambreForm()
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/hospitalisation/type_chambre_form.html', {'form': form , 'fonctionKey':fonctionKey})


# --------------------------------------------------------------------------------------------------
# VUE : Deuxième étape de la configuration de l'infrastructure de soins.
# FONCTION : Gère l'enregistrement des chambres physiques et de leurs prix par nuitée. Elle bloque
#            l'accès et réoriente l'utilisateur vers l'étape 1 si aucune catégorie n'existe en base.
# --------------------------------------------------------------------------------------------------
@login_required
def ajouter_chambre(request):
    """ Étape 2 : Enregistrer une chambre physique """
    # Sécurité métier : Empêche l'enregistrement d'une chambre orpheline sans type associé.
    if not TypeChambre.objects.exists():
        messages.warning(request, "Vous devez d'abord créer un Type de chambre avant d'ajouter une chambre.")
        return redirect('ajouter_type_chambre')

    if request.method == 'POST':
        form = ChambreForm(request.POST)
        if form.is_valid():
            chambre = form.save()
            messages.success(request, f"La chambre {chambre.nom} a été enregistrée.")
            # Redirection logique et fluide vers l'étape 3 (Ajout du mobilier / des lits)
            return redirect('ajouter_lit')
    else:
        form = ChambreForm()
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/hospitalisation/chambre_form.html', {'form': form, 'fonctionKey':fonctionKey})


# --------------------------------------------------------------------------------------------------
# VUE : Troisième et dernière étape de la configuration de l'infrastructure.
# FONCTION : Ajoute les unités d'accueil individuelles (Lits) dans les chambres. Gère la double 
#            possibilité de valider la saisie ou d'enchaîner sur un enregistrement en série.
# --------------------------------------------------------------------------------------------------
@login_required
def ajouter_lit(request):
    """ Étape 3 : Enregistrer un lit dans une chambre """
    # Sécurité métier : Interdit de créer un lit s'il n'y a aucun local physique pour le recevoir.
    if not Chambre.objects.exists():
        messages.warning(request, "Vous devez d'abord créer une chambre avant d'y ajouter des lits.")
        return redirect('ajouter_chambre')

    if request.method == 'POST':
        form = LitForm(request.POST)
        if form.is_valid():
            lit = form.save()
            messages.success(request, f"Le lit '{lit.nom_ou_code}' a bien été ajouté à la {lit.chambre}.")
            
            # Optimisation UX : Permet à l'agent de configurer rapidement plusieurs lits pour une même chambre 
            # sans subir de ruptures de navigation récurrentes vers le tableau de bord.
            if 'ajouter_autre' in request.POST:
                return redirect('ajouter_lit')
            return redirect('dashboard_chambres')
    else:
        form = LitForm()
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    return render(request, 'back-end/hospitalisation/lit_form.html', {'form': form , 'fonctionKey':fonctionKey})


# --------------------------------------------------------------------------------------------------
# VUE : Point d'entrée d'action unitaire et asynchrone (ou par redirection directe).
# FONCTION : Permet aux infirmiers ou gestionnaires d'annuler une occupation ou de bloquer temporairement
#            un lit à la volée depuis l'interface visuelle sans passer par un formulaire d'édition complet.
# --------------------------------------------------------------------------------------------------
@login_required
def toggle_statut_lit(request, lit_id):
    """ Action rapide pour occuper/libérer un lit depuis le dashboard """
    lit = get_object_or_404(Lit, id=lit_id)
    # Bascule booléenne de l'état d'occupation du lit
    lit.est_occupe = not lit.est_occupe
    lit.save()
    messages.info(request, f"Le statut du lit {lit.nom_ou_code} a été modifié.")
    return redirect('dashboard_chambres')


# =====================================================================================================
# REDIGE ORDONNANCE
# =====================================================================================================
@login_required
def enregistrer_ordonnance_view(request, triage_id):
    triage = get_object_or_404(SigneVital, id=triage_id)
    consultation = get_object_or_404(Consultation, triage=triage)
    
    # Récupération des examens liés à cette consultation
    examens_termines = Examen.objects.filter(consultation=consultation, statut='TERMINE')

    if request.method == 'POST':
        form = OrdonnanceForm(request.POST)
        
        # Récupération des listes du formulaire
        noms = request.POST.getlist('nom_medicament[]')
        posologies = request.POST.getlist('posologie[]')
        durees = request.POST.getlist('duree[]')

        if form.is_valid():
            try:
                with transaction.atomic():
                    ordonnance = form.save(commit=False)
                    ordonnance.consultation = consultation
                    ordonnance.save()
                    
                    # Enregistrement des lignes médicaments
                    for n, p, d in zip(noms, posologies, durees):
                        if n.strip():
                            LigneMedicament.objects.create(
                                ordonnance=ordonnance,
                                nom_medicament=n,
                                posologie=p,
                                duree=d
                            )
                    
                    triage.est_consulte = True
                    triage.save()
                    
                    messages.success(request, "Ordonnance enregistrée avec succès !")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Erreur base de données : {e}")
        else:
            messages.error(request, "Formulaire invalide.")

    return render(request, 'back-end/medecin/enregistrer_ordonnance.html', {
        'consultation': consultation,
        'examens_termines': examens_termines, # C'est ici que l'info arrive dans le HTML
        'form': OrdonnanceForm()
    })
#
# ===========================================================================================
# LISTE ORDONNANCE COTE MEDECIN
# ============================================================================================
@login_required
def liste_ordonnances_delivrees_view(request):
    """
    Affiche la liste des ordonnances (Modèle Ordonnance) prescrites par le médecin.
    Permet également de stopper un médicament spécifique.
    """
    
    # --- GESTION DES ACTIONS (POST) ---
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Action pour stopper TOUTE l'ordonnance ou un médicament
        if action == 'stopper_medicament':
            ligne_id = request.POST.get('ligne_id')
            motif = request.POST.get('motif_arret', 'Arrêté par le médecin')
            
            if ligne_id and ligne_id.isdigit():
                ligne = LigneMedicament.objects.filter(id=int(ligne_id)).first()
                if ligne:
                    ligne.statut = 'STOPPE'
                    ligne.motif_arret = motif
                    ligne.date_modification = timezone.now()
                    ligne.save()
                    messages.warning(request, f"Le médicament '{ligne.nom_medicament}' a été stoppé.")
            return redirect(request.path_info)

    # --- REQUÊTE GET : AFFICHAGE DEPUIS LE MODÈLE ORDONNANCE ---
    # On récupère toutes les ordonnances avec le patient lié, et on pré-charge ses médicaments
    ordonnances_medecin = Ordonnance.objects.select_related(
        'consultation__triage__patient'
    ).prefetch_related(
        'medicaments'
    ).order_by('-date_prescrite')

    # Gestion du rôle utilisateur pour la sidebar
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    context = {
        'ordonnances_medecin': ordonnances_medecin,
        'fonctionKey': fonctionKey
    }
    
    return render(request, 'back-end/medecin/liste_ordonnances_delivrees.html', context)
#
# ===========================================================================================
# LISTE ORDONNANCE COTE MEDECIN
# ============================================================================================
@login_required
def liste_ordonnances_prescrites_view(request):
    # Récupération optimisée avec le bon related_name 'medicaments'
    ordonnances = Ordonnance.objects.filter(type_ordonnance='DEFINITIVE').select_related(
        'consultation__triage__patient', 
        'consultation__medecin' 
    ).prefetch_related(
        'medicaments', # <--- CORRIGÉ ICI
        'consultation__examens__prestation',
        'consultation__examens__technicien'
    ).order_by('-id')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    context = {
        'ordonnances': ordonnances, 
        'fonctionKey': fonctionKey
    }
    return render(request, 'back-end/medecin/liste_ordonnances.html', context)

#
# ===========================================================================================
# HOSPITALISE PATIENT 
# ============================================================================================
@login_required
def admettre_patient(request):
    # Récupération du rôle pour le contexte (optimisation : on évite la requête si user n'est pas authentifié)
    fonctionKey = None
    if request.user.is_authenticated:
        role = Fonction.objects.filter(userKey=request.user).first()
        if role and role.fonctionKey:
            fonctionKey = role.fonctionKey.roleName

    if request.method == 'POST':
        form = HospitalisationForm(request.POST)
        if form.is_valid():
            patient = form.cleaned_data.get('patient')
            
            # Vérification de sécurité : le patient a-t-il payé sa fiche ?
            if not patient.fiche_payee:
                messages.error(request, "Impossible d'admettre ce patient : fiche non payée.")
                return render(request, 'back-end/hospitalisation/admettre.html', {
                    'form': form, 
                    'fonctionKey': fonctionKey
                })

            # Sauvegarde
            try:
                hospitalisation = form.save()
                messages.success(request, "Admission réussie et lit réservé.")
                return redirect('liste_hospitalisations')
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de l'enregistrement : {str(e)}")
        else:
            messages.error(request, "Erreur lors de l'admission. Veuillez vérifier les champs du formulaire.")
    else:
        form = HospitalisationForm()

    return render(request, 'back-end/hospitalisation/admettre.html', {
        'form': form, 
        'fonctionKey': fonctionKey
    })

#
# ===========================================================================================
# LISTE DES PATIENT HOSPITALISE
# ============================================================================================
@login_required
def liste_hospitalisations(request):
    # Correction : Le chemin complet vers le type de chambre est 'lit__chambre__type_chambre'
    # 'patient' et 'lit' sont déjà inclus dans la chaîne.
    hospitalisations = Hospitalisation.objects.select_related(
        'patient', 
        'lit__chambre__type_chambre'
    ).order_by('-date_entree')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/hospitalisation/liste_hospitalisations.html', {
        'hospitalisations': hospitalisations,
        'fonctionKey': fonctionKey
    })


#
# ===========================================================================================
# DOSSIER MEDICALE
# ============================================================================================
@login_required
def dossier_medical_complet(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if not patient.fiche_payee:
        messages.error(request, "Accès refusé.")
        return redirect('liste_patients')
    
    # Consultations
    historique_consultations = Consultation.objects.filter(
        triage__patient=patient
    ).order_by('-date_creation').prefetch_related(
        'examens__prestation', 
        'ordonnance_set__medicaments'
    ).select_related('triage', 'medecin')
    
    # Hospitalisations (on retire le prefetch qui causait l'erreur)
    hospitalisations = Hospitalisation.objects.filter(patient=patient).order_by('-date_entree')
    
    # Signes vitaux (on s'assure que 'infirmier' existe ou on le retire)
    signes_vitaux = SigneVital.objects.filter(patient=patient).order_by('-date_prelevement')
    
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    context = {
        'patient': patient,
        'consultations': historique_consultations,
        'hospitalisations': hospitalisations,
        'signes_vitaux': signes_vitaux,
        'fonctionKey':fonctionKey
    }
    
    return render(request, 'back-end/patient/dossier_medical.html', context)


#
# ===========================================================================================
# DETAIL HOSPITALIERE
# ============================================================================================
@login_required
def detail_hospitalisation(request, pk):
    # On garde ton select_related pour optimiser l'hospitalisation
    hosp = get_object_or_404(
        Hospitalisation.objects.select_related('patient', 'lit__chambre__type_chambre'), 
        pk=pk
    )
    
    # 1. On récupère TOUTES les ordonnances du patient, triées par date (récentes d'abord)
    # 2. On utilise prefetch_related pour charger les médicaments en une seule fois
    ordonnances = Ordonnance.objects.filter(
        consultation__triage__patient=hosp.patient
    ).prefetch_related('medicaments').order_by('-date_prescrite')
    
    # Récupérer tout le carnet de suivi
    suivis = hosp.suivis_journaliers.all()
    
    # Gestion du rôle (optimisable via un middleware plus tard, mais OK pour le moment)
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/hospitalisation/detail.html', {
        'hosp': hosp,
        'ordonnances': ordonnances, # On passe la liste
        'suivis': suivis, 
        'fonctionKey': fonctionKey
    })
#
# ===========================================================================================
# ADD SUIVI
# ============================================================================================
@login_required
def ajouter_suivi(request, pk):
    if request.method == 'POST':
        hosp = get_object_or_404(Hospitalisation, pk=pk)
        
        # Récupération sécurisée avec vérification minimale
        constantes = request.POST.get('constantes_du_jour')
        etat = request.POST.get('etat_general')
        
        if constantes and etat:
            SuiviQuotidien.objects.create(
                hospitalisation=hosp,
                infirmier=request.user,
                etat_general=etat,
                constantes_du_jour=constantes,
                soins_effectues=request.POST.get('soins_effectues', '') # Optionnel
            )
            messages.success(request, "Suivi quotidien enregistré.")
        else:
            messages.error(request, "Veuillez remplir au moins les constantes et l'état général.")
            
        return redirect('detail_hospitalisation', pk=pk)

#
# ===========================================================================================
# IMPRIMER ORDONNANCE 
# ============================================================================================
@login_required
def imprimer_ordonnance(request, ordonnance_id):
    # Récupération de l'ordonnance avec ses relations pré-chargées
    ordonnance = get_object_or_404(
        Ordonnance.objects.select_related(
            'consultation__triage__patient', 
            'consultation__medecin'
        ).prefetch_related(
            'medicaments' # Utilisation du related_name
        ), 
        id=ordonnance_id
    )
    
    context = {'ord': ordonnance}
    return render(request, 'back-end/imprimer/print_ordonnance.html', context)


#
# ===========================================================================================
# CREE UN ORDONNANCE
# ============================================================================================
@login_required
def creer_ordonnance_view(request, consultation_id):
    # 1. Récupération sécurisée de la consultation
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # 2. Traitement du formulaire POST
    if request.method == 'POST':
        diagnostic = request.POST.get('diagnostic_final')
        contenu = request.POST.get('contenu_ordonnance')
        type_ord = request.POST.get('type_ordonnance')
        
        # Listes dynamiques des médicaments
        noms = request.POST.getlist('nom_medicament[]')
        posologies = request.POST.getlist('posologie[]')
        durees = request.POST.getlist('duree[]')

        try:
            with transaction.atomic():
                # Mise à jour du diagnostic
                consultation.diagnostic_final = diagnostic
                consultation.save()
                
                # Création de l'ordonnance
                ordonnance = Ordonnance.objects.create(
                    consultation=consultation,
                    observation=contenu,
                    type_ordonnance=type_ord
                )
                
                # Enregistrement des médicaments
                for nom, pos, dur in zip(noms, posologies, durees):
                    if nom.strip(): # On n'enregistre que si le nom est présent
                        Medicament.objects.create(
                            ordonnance=ordonnance,
                            nom=nom,
                            posologie=pos,
                            duree=dur
                        )
            
            messages.success(request, f"Ordonnance créée pour {consultation.triage.patient.noms}.")
            return redirect('liste_attente_medecin') # Remplacez par votre vrai nom d'URL
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")

    # 3. Affichage du formulaire (GET)

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/medecin/creer_ordonnance.html', {'c': consultation, 'fonctionKey': fonctionKey}) 



#
# ======================================================================================
# ENREGISTREMENT DE L'ENTREPRISE
# ======================================================================================
@login_required
def enregistrer_entreprise_view(request):
    if request.method == 'POST':
        form = EntrepriseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "L'entreprise a été enregistrée avec succès.")
            return redirect('liste_entreprises') # Remplacez par votre URL de redirection
    else:
        form = EntrepriseForm()
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/entreprise/enregistrer_entreprise.html', {'form': form , 'fonctionKey':fonctionKey})

#
# ======================================================================================
# LISTE DES ENTREPRISES
# ======================================================================================
@login_required
def liste_entreprises_view(request):
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    entreprises = Entreprise.objects.all().order_by('-date_enregistrement')
    return render(request, 'back-end/entreprise/liste_entreprises.html', {'entreprises': entreprises, 'fonctionKey':fonctionKey})


#
# ======================================================================================
# MEDECIN ORDONNANCE D'URGENCES
# ======================================================================================
@login_required
def enregistrer_ordonnance_urgence(request, patient_id):
    # On récupère le patient par son ID
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        diagnostic = request.POST.get('diagnostic')
        observation = request.POST.get('observation')
        
        noms = request.POST.getlist('nom')
        posologies = request.POST.getlist('posologie')
        durees = request.POST.getlist('duree')

        with transaction.atomic():
            # Cas A : Si vous voulez lier à la dernière consultation du patient
            # consultation = Consultation.objects.filter(triage__patient=patient).latest('date_creation')
            
            # Cas B : Création d'une consultation d'urgence si aucune n'est active
            consultation = Consultation.objects.create(
                triage=patient.triage_set.latest('id'), # Assurez-vous d'avoir ce lien
                medecin=request.user,
                motif_consultation="Urgence médicale"
            )

            ordonnance = Ordonnance.objects.create(
                consultation=consultation,
                type_ordonnance='URGENCE',
                diagnostic=diagnostic,
                observation=observation
            )
            
            for i in range(len(noms)):
                if noms[i]:
                    Medicament.objects.create(
                        ordonnance=ordonnance,
                        nom=noms[i],
                        posologie=posologies[i],
                        duree=durees[i]
                    )
        
        return redirect('detail_patient', pk=patient.pk)
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/medecin/creer_ordonnance_urgence.html', {
        'patient': patient ,
        'fonctionKey' : fonctionKey
    })


#
# ======================================================================================
#  PATIENT PAR LE MEDECIN POUR ORDONNANCE D'URGENCE
# ======================================================================================
@login_required
def liste_patients_urgence(request):
    # 1. On filtre pour ne garder QUE les patients dont fiche_payee est True
    patients = Patient.objects.filter(fiche_payee=True).order_by('-id')
    
    # 2. Récupération du rôle
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    # 3. Enrichissement
    for p in patients:
        # Consultation la plus récente
        p.consultation_active = Consultation.objects.filter(
            triage__patient=p
        ).order_by('-date_creation').first()
        
        # Hospitalisation en cours
        p.hosp_en_cours = Hospitalisation.objects.filter(
            patient=p, 
            statut='EN_COURS'
        ).first()

    return render(request, 'back-end/medecin/liste_patients.html', {
        'patients': patients, 
        'fonctionKey': fonctionKey
    })




# 
# ===========================================================================================
# IMPRIMER LES RESULTAT DU TECHNICIEN 
# ===========================================================================================
@login_required
def imprimer_resultat(request, examen_id):
    # On récupère directement l'examen par son ID
    examen = get_object_or_404(DemandeExamen.objects.select_related('consultation__triage__patient', 'prestation', 'technicien'), id=examen_id)
    
    # Comme vous avez besoin de la consultation pour le template, on l'extrait de l'examen
    consultation = examen.consultation
    
    # On met l'examen dans une liste pour conserver la compatibilité avec votre template (qui fait un {% for exam in examens %})
    examens = [examen]
    
    return render(request, 'back-end/medecin/imprimer_resultat.html', {
        'consultation': consultation,
        'examens': examens
    })
# 
# ===========================================================================================
# IMPRIMER LES RESULTAT DU TECHNICIEN TOUT 
# ===========================================================================================
@login_required
def imprimer_consultation(request, consultation_id):
    # On ne récupère que la consultation et ses examens
    consultation = get_object_or_404(
        Consultation.objects.prefetch_related('examens'), 
        id=consultation_id
    )
    
    # On filtre uniquement les examens terminés pour l'affichage
    examens_termines = consultation.examens.filter(statut='TERMINE')
    
    return render(request, 'back-end/medecin/imprimer_consultation.html', {
        'consultation': consultation,
        'examens': examens_termines
    })

# 
# ============================================================================================
# MODIFICATION DES L'ORDONNANCE
# ============================================================================================
@login_required
def modifier_ordonnance_view(request, ordonnance_id):
    # Récupération de l'ordonnance avec ses relations
    ordonnance = get_object_or_404(Ordonnance.objects.select_related('consultation'), id=ordonnance_id)

    if request.method == 'POST':
        # 1. Mise à jour des informations de base
        ordonnance.type_ordonnance = request.POST.get('type_ordonnance')
        ordonnance.observation = request.POST.get('observation')
        ordonnance.save()

        # 2. Mise à jour des médicaments : on supprime les anciens et on recrée
        ordonnance.medicaments.all().delete()
        
        noms = request.POST.getlist('nom_medicament[]')
        posologies = request.POST.getlist('posologie[]')
        durees = request.POST.getlist('duree[]')

        for i in range(len(noms)):
            if noms[i]: # On vérifie que le nom n'est pas vide
                Medicament.objects.create(
                    ordonnance=ordonnance,
                    nom=noms[i],
                    posologie=posologies[i],
                    duree=durees[i]
                )
        
        messages.success(request, "Ordonnance mise à jour avec succès.")
        return redirect('liste_ordonnances_prescrites_view') 
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/medecin/modifier_ordonnance.html', {'ord': ordonnance, 'fonctionKey':fonctionKey})


#
# ====================================================================================================
#  ADMETTRE UNE PATIENTE A LA MATERNITE 
# ====================================================================================================
@login_required
def admettre_maternite(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # SÉCURITÉ 1 : Vérification stricte du paiement de la fiche générale
    if not patient.fiche_payee:
        messages.error(request, "Erreur : La fiche du patient doit être réglée avant toute admission.")
        return redirect('enregistrement_patient')

    # SÉCURITÉ 2 : Vérification stricte du sexe
    if patient.sexe not in ['Feminin', 'F']:
        messages.error(request, "Erreur : Impossible d'admettre un homme en maternité.")
        return redirect('enregistrement_patient')

    maternite_instance = Maternite(patient=patient)
    
    if request.method == 'POST':
        form = MaterniteForm(request.POST, instance=maternite_instance)
        if form.is_valid():
            dossier = form.save(commit=False)
            dossier.enregistre_par = request.user
            
            # MISE À JOUR LOGIQUE : Initialisation du statut de paiement
            # Par défaut, le dossier est à False tant que la caisse ne confirme pas
            dossier.est_paye = False 
            
            dossier.save()
            
            messages.success(request, f"Patiente {patient.noms} admise. Veuillez procéder au paiement des frais d'ouverture.")
            return redirect('liste_admissions_maternite') # On redirige vers la liste pour voir le statut
    else:
        form = MaterniteForm(instance=maternite_instance)
    
    # Récupération du rôle
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/maternite/admettre.html', {
        'form': form, 
        'patient': patient,
        'fonctionKey': fonctionKey
    })



# 
# ========================================================================================
#  LISTE DE PATIENTES A LA MATERNITES 
# ========================================================================================
@login_required
def liste_admissions_maternite(request):
    # Récupère tous les dossiers, ordonnés du plus récent au plus ancien
    admissions = Maternite.objects.all().order_by('-date_admission')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    context = {
        'admissions': admissions,
        'segment': 'liste_maternite' ,
        'fonctionKey' : fonctionKey
    }
    return render(request, 'back-end/maternite/liste_maternite.html', context)


# 
# ========================================================================================
# PAYER DOSSIER MATERNITE
# ========================================================================================
@login_required
def payer_dossier_maternite(request, dossier_id):
    dossier = get_object_or_404(Maternite, id=dossier_id)
    
    # Récupération des données pour le formulaire
    prestation_mat = Prestation.objects.filter(categorie='MAT').first()
    prix_referentiel = prestation_mat.prix if prestation_mat else Decimal('150.00')
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else Decimal('2500.00')
    
    if request.method == 'POST':
        # On récupère les valeurs
        montant_raw = request.POST.get('montant', '0')
        reste_raw = request.POST.get('reste_a_payer', '0')
        devise = request.POST.get('devise', 'USD')
        
        try:
            # Conversion sécurisée en Decimal
            montant = Decimal(montant_raw)
            reste = Decimal(reste_raw)
            
            # Conversion du montant versé en USD pour comparaison
            montant_en_usd = montant if devise == 'USD' else (montant / taux)
            
            # Vérification de sécurité
            if montant_en_usd > prix_referentiel:
                messages.error(request, f"Erreur : Le montant versé dépasse le forfait Maternité de {prix_referentiel} USD.")
                return redirect('payer_dossier_maternite', dossier_id=dossier.id)
            
            # Création du paiement
            Paiement.objects.create(
                patient=dossier.patient,
                dossier_maternite=dossier,
                service='MATERNITE',
                montant_verse=montant,
                devise=devise,
                reste_a_payer=reste,
                caissier=request.user
            )
            
            messages.success(request, f"Paiement de {montant} {devise} enregistré avec succès.")
            return redirect('liste_admissions_maternite')
            
        except (InvalidOperation, ValueError, TypeError):
            # En cas de valeur non numérique, on renvoie une erreur
            messages.error(request, "Erreur : Format de montant invalide.")
            return redirect('payer_dossier_maternite', dossier_id=dossier.id)
    
    # Affichage de la page en GET
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/maternite/payer.html', {
        'dossier': dossier, 
        'prix_max': prix_referentiel,
        'taux': taux ,
        'fonctionKey' : fonctionKey
    })



#  
# =================================================================================================
# ENREGISTREMENT DE L'ACTE DE DECES 
# =================================================================================================
@login_required
def enregistrer_deces(request):
    patients = Patient.objects.all().order_by('noms')

    if request.method == 'POST':
        try:
            # Récupération de l'identité
            patient_id = request.POST.get('patient_id')
            nom_externe = request.POST.get('nom_patient_externe')
            
            # Récupération des infos biographiques et adresse
            date_naissance = request.POST.get('date_naissance')
            lieu_naissance = request.POST.get('lieu_naissance')
            adresse_avenue = request.POST.get('adresse_avenue')
            adresse_numero = request.POST.get('adresse_numero')
            adresse_quartier = request.POST.get('adresse_quartier')
            adresse_commune = request.POST.get('adresse_commune')
            
            # Infos décès
            date_deces = request.POST.get('date_deces')
            cause = request.POST.get('cause_deces')
            
            # Certification
            etablissement = request.POST.get('etablissement', "Hôpital Paradis Center")
            certifie = request.POST.get('certifie_par')
            numero_cnom = request.POST.get('numero_cnom')
            notes = request.POST.get('notes', '')

            # Validation (vérifie au moins les champs essentiels)
            if not date_deces or not cause or not certifie:
                messages.error(request, "Veuillez remplir tous les champs obligatoires (Date décès, Cause, Médecin).")
                return redirect('enregistrer_deces')

            # Création de l'objet avec tous les nouveaux champs
            Deces.objects.create(
                patient_id=patient_id if patient_id else None,
                nom_patient_externe=nom_externe if not patient_id else None,
                date_naissance=date_naissance,
                lieu_naissance=lieu_naissance,
                adresse_avenue=adresse_avenue,
                adresse_numero=adresse_numero,
                adresse_quartier=adresse_quartier,
                adresse_commune=adresse_commune,
                date_deces=date_deces,
                cause_deces=cause,
                etablissement=etablissement,
                certifie_par=certifie,
                numero_cnom=numero_cnom,
                notes=notes
            )

            messages.success(request, "Certificat de décès enregistré avec succès.")
            return redirect('liste_deces')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement : {str(e)}")
            return redirect('enregistrer_deces')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/deces/enregistre.html', {'patients': patients, 'fonctionKey': fonctionKey})

#
# =========================================================================
# LISTE DES DECES 
# ========================================================================
@login_required
def liste_deces(request):
    # On récupère tous les décès, triés par date (du plus récent au plus ancien)
    deces_list = Deces.objects.all().order_by('-date_deces')

    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None
    return render(request, 'back-end/deces/liste.html', {'deces_list': deces_list, 'fonctionKey': fonctionKey})

#
# ==============================================================================
# IMPRIMER DECES 
# =============================================================================
@login_required
def imprimer_deces(request, deces_id):
    deces = get_object_or_404(Deces, id=deces_id)
    return render(request, 'back-end/deces/imprimer.html', {'deces': deces})


#
# =============================================================================
# PAYER DECES ACTE
# =============================================================================
@login_required
def enregistrer_paiement_deces(request, deces_id):
    deces = get_object_or_404(Deces, id=deces_id)
    
    # 1. VÉRIFICATION DU DOUBLON : Est-ce qu'un paiement existe déjà pour ce décès ?
    if deces.paiements.exists():
        messages.warning(request, "Attention : Ce décès a déjà été réglé.")
        return redirect('liste_deces')

    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else Decimal('2500.00')
    
    prestation = Prestation.objects.filter(libelle__icontains="acte de deces").first()
    prix_usd = prestation.prix if prestation else Decimal('0.00')
    prix_cdf = (prix_usd * taux).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    if request.method == 'POST':
        devise = request.POST.get('devise')
        try:
            montant_verse = Decimal(request.POST.get('montant_verse', '0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            montant_verse = Decimal('0')
            
        prix_requis = (prix_usd if devise == 'USD' else prix_cdf).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 2. VÉRIFICATION DU MONTANT
        if abs(montant_verse - prix_requis) > Decimal('0.05'): 
            messages.error(request, f"Paiement refusé : Le montant doit être de {prix_requis:.2f} {devise}.")
            return render(request, 'back-end/deces/payer.html', {
                'deces': deces, 'prix_usd': prix_usd, 'prix_cdf': prix_cdf, 'taux': taux
            })

        # 3. CRÉATION DU PAIEMENT (Double sécurité au cas où deux clics simultanés arrivent)
        if not deces.paiements.exists():
            Paiement.objects.create(
                patient=deces.patient if deces.patient else None,
                deces=deces,
                service='DECES',
                montant_verse=montant_verse,
                devise=devise,
                caissier=request.user
            )
            messages.success(request, "Paiement enregistré avec succès.")
        else:
            messages.error(request, "Erreur : Un paiement a été enregistré simultanément.")
            
        return redirect('liste_deces')

    # Affichage normal
    role = Fonction.objects.filter(userKey=request.user).first()
    fonctionKey = role.fonctionKey.roleName if role and role.fonctionKey else None

    return render(request, 'back-end/deces/payer.html', {
        'deces': deces, 'prix_usd': prix_usd, 'prix_cdf': prix_cdf, 
        'taux': taux, 'fonctionKey': fonctionKey
    })