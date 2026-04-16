from django.shortcuts import render , redirect , get_object_or_404 , HttpResponse 
from .forms import * 
from django.contrib.auth import authenticate , login as auth , logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User
from .models import *
from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum, F , Q , Count
from django.forms import inlineformset_factory
from django.db import transaction 
from datetime import timedelta , datetime
from django.utils import timezone
import json
from django.http import JsonResponse
from django.contrib.auth.forms import SetPasswordForm , PasswordChangeForm

# Create your views here.


# 1
# ============================================
# ============================================
# home page d'acueil

def home(request):
    return render(request , 'front-end/index.html')

# 2
#==============================================================
# login 
# =============================================================
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
                return redirect('panel') 
            else:
                msg = "mot de passe erronne !!!:🤞"
    form = LoginForm()
    return render(request, 'back-end/login.html', {'form':form , 'msg':msg})  

# 3
# ========================================================================
# dashboard
# =========================================================================
@login_required()
def panel(request):
    # nombre des user 
    use = User.objects.all().count()

    # nombre de patient
    patient = Patient.objects.all().count

    # profil 
    # 
    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    context = {
    'nbrU' : use ,
    'fonction': fonction ,
    'nbrP' : patient , 
    } 
    return render(request , 'back-end/index.html', context)

# 4 
# ==========================================================================
# deconnexion
# ==========================================================================
def deconnexion(request):
    logout(request)
    return redirect('home') 

# 5 
# ===========================================================================
# ajout utilisateur 
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
    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    return render(request,'back-end/add-employee.html',{'fonction':fonction, 'form':form, 'msg':msg}) 

# 6
# ==================================================================================
# liste des employee
# ==================================================================================
@login_required()
def employeRead(request):

    # liste des user
    userListe = User.objects.all() 

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    context = {
        'fonction': fonction , 
        'userListe' : userListe,
    }

    return render(request , 'back-end/employees.html' ,context)

# 7
# ==================================================================================
# employee profil attribution 
# ==================================================================================
@login_required()
def profilAdd(request, user_id):
    pro = get_object_or_404(User , id = user_id)
    prof , created = Profil.objects.get_or_create(userProfil = pro)
    msg = None 

    if request.method == 'POST':
        form = ProfilAddForm(request.POST , instance = prof)

        if form.is_valid():
            p = form.save(commit=False)
            p.userProfil = pro 
            p.save()

            return redirect('employeRead')

    form = ProfilAddForm(instance = prof)

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 


    context = {
        'form': form ,
        'fonction' : fonction ,

    }

    return render(request,'back-end/profil-add-employe.html',context)
# 8
# ======================================================================
# liste des employes avec leur profil
# ======================================================================
@login_required()
def profilRead(request):
    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    profilRead = Profil.objects.all()

    context = {
        'fonction' : fonction , 
        'profilRead' : profilRead
    }

    return render(request , 'back-end/profil-read-employe.html',context)


# 9 
# ======================================================================
# ajoute patient 
# ======================================================================
@login_required()
def patientAdd(request):

    msg = None 
    if request.method == 'POST':
        form = PatientAddForm(request.POST)

        if form.is_valid():
            form.save()

            msg = "Patient(e) enregistre"
            form = PatientAddForm(request.POST)
    form = PatientAddForm()


    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    return render(request , 'back-end/add-patient.html' , {'fonction': fonction, 'form':form,'msg':msg})

# 10 
# ==========================================================================
# liste de patient(e)
# ==========================================================================
@login_required()
def patientRead(request):

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None

    # liste de patient
    patientListe = Patient.objects.all()

    context = {
        'fonction' : fonction , 
        'patientListe' : patientListe
    }

    return render(request, 'back-end/patient-liste.html',context)

# 11 
# ===================================================================
# paiement de la fiche
# ===================================================================
@login_required()
def encaisser_fiche(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # 1. Récupération des données en base
    prestation_fiche = Prestation.objects.filter(categorie='ADM').first()
    deja_paye = Facture.objects.filter(patient=patient, prestation__categorie='ADM').exists()
    
    # Récupération du taux depuis ton modèle ConfigurationHopital
    config = ConfigurationHopital.objects.first()
    TAUX = config.taux_usd_en_cdf if config else 2500.00 # 2500 par défaut si vide

    error_message = None
    if not prestation_fiche:
        error_message = "Erreur : La prestation de catégorie 'ADM' (Fiche) n'est pas configurée."

    if request.method == 'POST' and not error_message and not deja_paye:
        form = PaiementFicheForm(request.POST)
        if form.is_valid():
            montant_saisi = form.cleaned_data.get('montant_physique')
            devise = form.cleaned_data.get('devise')
            prix_fiche_cdf = prestation_fiche.prix_cdf

            # 2. Logique de conversion pour la vérification
            montant_en_cdf = montant_saisi
            if devise == 'USD':
                montant_en_cdf = montant_saisi * TAUX

            # 3. Vérification stricte du montant
            if montant_en_cdf > prix_fiche_cdf:
                if devise == 'USD':
                    max_usd = prix_fiche_cdf / TAUX
                    form.add_error('montant_physique', f"Trop élevé. Le max est de {max_usd:.2f} USD")
                else:
                    form.add_error('montant_physique', f"Trop élevé. Le max est de {prix_fiche_cdf} CDF")
            else:
                # 4. Création de la facture et enregistrement du paiement
                nouvelle_facture = Facture.objects.create(
                    patient=patient,
                    prestation=prestation_fiche
                )
                paiement = form.save(commit=False)
                paiement.facture = nouvelle_facture
                # On peut stocker le montant converti si ton modèle Paiement a un champ dédié
                paiement.save()
                
                return redirect('patientRead')
    else:
        form = PaiementFicheForm()


    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/encaisser.html', {
        'form': form,
        'patient': patient,
        'prestation': prestation_fiche,
        'deja_paye': deja_paye,
        'taux': TAUX,
        'error_message': error_message , 
        'fonction' : fonction
    })

# 12
# =================================================================================================
# historique du paiement de patient 
# =================================================================================================
@login_required()
def historique_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    config = ConfigurationHopital.objects.first()
    taux = Decimal(str(config.taux_usd_en_cdf)) if config else Decimal("2500.0")
    
    # --- PARTIE TRAITEMENT DES PAIEMENTS (POST) ---
    if request.method == "POST":
        facture_id = request.POST.get('facture_id')
        montant_saisi = request.POST.get('montant')
        devise = request.POST.get('devise')
        
        if facture_id and montant_saisi:
            try:
                with transaction.atomic():
                    f_obj = Facture.objects.select_related('prestation').get(id=facture_id)
                    
                    # 1. Calcul du déjà payé sur CETTE facture
                    total_deja_verse = Decimal("0.0")
                    for p in f_obj.paiements.all():
                        m_p = Decimal(str(p.montant_physique))
                        total_deja_verse += (m_p * taux) if p.devise == 'USD' else m_p
                    
                    # 2. Reste réel avant le nouveau paiement
                    prix_total_facture = Decimal(str(f_obj.prestation.prix_cdf))
                    reste_a_solder = prix_total_facture - total_deja_verse
                    
                    # 3. Conversion du nouveau montant
                    nouveau_val = Decimal(str(montant_saisi))
                    nouveau_en_cdf = (nouveau_val * taux) if devise == 'USD' else nouveau_val

                    # 4. SÉCURITÉ : Ne pas payer plus que le reste
                    if nouveau_en_cdf > (reste_a_solder + Decimal("0.1")):
                        messages.error(request, f"Montant trop élevé ! Il ne reste que {int(reste_a_solder)} FC à payer.")
                    elif nouveau_en_cdf <= 0:
                        messages.error(request, "Veuillez saisir un montant valide.")
                    else:
                        # 5. Création du paiement
                        Paiement.objects.create(
                            facture=f_obj,
                            montant_physique=nouveau_val,
                            devise=devise
                        )
                        
                        # 6. LOGIQUE DE LIBÉRATION AU LABO (Examen par examen)
                        # On recalcule le total payé pour CETTE prestation spécifique
                        nouveau_total_paye = total_deja_verse + nouveau_en_cdf
                        
                        # Si le montant couvre le prix de l'examen, on le libère
                        if nouveau_total_paye >= (prix_total_facture - Decimal("0.1")):
                            ExamenPrescrit.objects.filter(
                                consultation__patient=patient, 
                                prestation=f_obj.prestation, 
                                paye=False
                            ).update(paye=True)
                            messages.success(request, f"Paiement validé. L'examen '{f_obj.prestation.libelle}' est envoyé au labo !")
                        else:
                            reste_final = prix_total_facture - nouveau_total_paye
                            messages.info(request, f"Acompte enregistré. Reste à payer pour cet examen : {int(reste_final)} FC.")

            except Exception as e:
                messages.error(request, f"Erreur système : {str(e)}")
            
            return redirect('historique_patient', patient_id=patient.id)

    # --- PARTIE AFFICHAGE (GET) ---
    factures = Facture.objects.filter(patient=patient).select_related('prestation').prefetch_related('paiements').order_by('-id')
    
    for f in factures:
        total_verse_f = Decimal("0.0")
        for p in f.paiements.all():
            m_p_aff = Decimal(str(p.montant_physique))
            total_verse_f += (m_p_aff * taux) if p.devise == 'USD' else m_p_aff
        
        # Attributs pour le template HTML
        f.somme_payee = total_verse_f 
        f.montant_restant = Decimal(str(f.prestation.prix_cdf)) - total_verse_f
        f.est_soldee = f.montant_restant <= Decimal("0.1")

    # Gestion du profil pour le header/sidebar
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/historique_patient.html', {
        'patient': patient, 
        'factures': factures, 
        'taux': taux, 
        'profil': profil,
        'fonction': fonction
    })

# 13
# =========================================================================
# imprimer recu
# =========================================================================
@login_required()
def imprimer_recu(request, paiement_id):
    paiement = get_object_or_404(Paiement, id=paiement_id)
    return render(request, 'back-end/recu_paiement.html', {'paiement': paiement})
# 14
# ===========================================================================
# facture global
# ===========================================================================
@login_required()
def imprimer_facture_globale(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)
    
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2250
    
    total_verse = 0
    for p in facture.paiements.all():
        if p.devise == 'USD':
            total_verse += (p.montant_physique * taux)
        else:
            total_verse += p.montant_physique
    
    # On calcule les montants sans toucher aux attributs du modèle
    somme_deja_payee = total_verse
    montant_du_reste = facture.prestation.prix_cdf - total_verse
    
    return render(request, 'back-end/facture_globale.html', {
        'facture': facture,
        'somme_deja_payee': somme_deja_payee,
        'montant_du_reste': montant_du_reste,
        'taux': taux
    })

# 15 
# =================================================================================
# listes de patient qui on solde la fiche 
# =================================================================================
@login_required()
def liste_patients_soldes(request):
    # Optimisation : on charge les paiements et la prestation pour éviter les requêtes répétitives
    toutes_factures = Facture.objects.select_related('patient', 'prestation').prefetch_related('paiements').all()
    
    config = ConfigurationHopital.objects.first()
    taux = Decimal(str(config.taux_usd_en_cdf)) if config else Decimal("2250.0")
    
    patients_prets = []

    for f in toutes_factures:
        # --- FILTRE : On ne traite QUE si la prestation est une "Fiche" ---
        # .upper() permet d'éviter les erreurs de casse (Fiche vs fiche)
        if "FICHE" not in f.prestation.libelle.upper():
            continue  # On passe à la facture suivante si ce n'est pas une fiche

        # Calcul du total payé
        total_paye = Decimal("0.0")
        for p in f.paiements.all():
            m_p = Decimal(str(p.montant_physique))
            if p.devise == 'USD':
                total_paye += (m_p * taux)
            else:
                total_paye += m_p
        
        # Vérification si la facture est soldée
        prix_total = Decimal(str(f.prestation.prix_cdf))
        if total_paye >= prix_total:
            patients_prets.append({
                'patient': f.patient,
                'prestation': f.prestation.libelle,
                'date': f.date_emission,
                'facture_id': f.id
            })

    # Récupération du profil
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    return render(request, 'back-end/infirmier_signes.html', {
        'patients_prets': patients_prets, 
        'fonction': fonction 
    })

# 16 
# =================================================================================
# prendre le signe vitaux
# =================================================================================
@login_required()
def prendre_signes(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    aujourdhui = timezone.now().date()
    
    instance_existante = SignesVitaux.objects.filter(
        patient=patient, 
        date_prelevement__date=aujourdhui
    ).first()

    if request.method == "POST":
        form = SignesVitauxForm(request.POST, instance=instance_existante)
        if form.is_valid():
            signes = form.save(commit=False)
            signes.patient = patient
            signes.infirmier = request.user
            signes.save()
            
            if instance_existante:
                messages.info(request, f"Les constantes de {patient.noms} ont été mises à jour.")
            else:
                messages.success(request, f"Les constantes de {patient.noms} ont été enregistrées.")
                
            # CORRECTION ICI : Le nom doit correspondre au 'name' dans urls.py
            return redirect('liste_soldes') 
            
    else:
        form = SignesVitauxForm(instance=instance_existante)

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/formulaire_signes.html', {
        'form': form,
        'patient': patient,
        'est_modification': instance_existante is not None,
        'fonction': fonction
    })

# 17 
# =========================================================================================================
# historique de signe vitaux par les infirmier
# =========================================================================================================
@login_required()
def historique_signes_vitaux(request):
    query = request.GET.get('search')
    historique = SignesVitaux.objects.all().select_related('patient', 'infirmier').order_by('-date_prelevement')

    if query:
        # On filtre par nom du patient OU par nom d'utilisateur de l'infirmier
        historique = historique.filter(
            models.Q(patient__noms__icontains=query) | 
            models.Q(infirmier__username__icontains=query)
        )

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None
    
    return render(request, 'back-end/historique_signes.html', {'historique': historique , 'fonction' : fonction})

# 18 
# ==============================================================================================================
# liste d'attente LA LISTE D'ATTENTE (Ce que le médecin voit en premier)
# ==============================================================================================================
@login_required()
def liste_attente_medecin(request):
    # On récupère les signes vitaux sans consultation
    patients_en_attente = SignesVitaux.objects.select_related('patient', 'infirmier').filter(
        consultation__isnull=True
    ).order_by('-date_prelevement')

    query = request.GET.get('search')
    if query:
        # Utilisation de 'noms' (avec un s) comme dans ton historique
        patients_en_attente = patients_en_attente.filter(
            Q(patient__noms__icontains=query) | 
            Q(patient__prenom__icontains=query)
        )

    # Récupération du profil pour le menu/sidebar
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None
    
    return render(request, 'back-end/liste_attente.html', {
        'patients_en_attente': patients_en_attente, 
        'fonction': fonction
    })


# 19 
# =============================================================================================================
# preparation du consultaion par le medecin tout en recuperant le signe vitaux
# =============================================================================================================
@login_required()
def effectuer_consultation(request, sv_id):
    signes = get_object_or_404(SignesVitaux, id=sv_id)
    patient = signes.patient
    
    prestations_labo = Prestation.objects.filter(
        Q(categorie__iexact='LABO') | Q(categorie__iexact='Laboratoire')
    )

    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        
        if form.is_valid():
            try:
                # Maintenant que 'transaction' est importé, ceci va marcher :
                with transaction.atomic():
                    consultation = form.save(commit=False)
                    consultation.patient = patient
                    consultation.signes_vitaux = signes
                    consultation.medecin = request.user
                    consultation.save()

                    examens_ids = request.POST.getlist('examens_choisis')
                    for e_id in examens_ids:
                        prestation = Prestation.objects.get(id=e_id)
                        qty = request.POST.get(f'qty_{e_id}', 1)
                        
                        ExamenPrescrit.objects.create(
                            consultation=consultation,
                            prestation=prestation,
                            quantite=int(qty)
                        )
                
                messages.success(request, "Consultation et examens enregistrés !")
                return redirect('liste_attente_medecin')

            except Exception as e:
                messages.error(request, f"Erreur technique : {e}")
        else:
            messages.error(request, "Le formulaire est invalide. Vérifiez les champs.")
    else:
        form = ConsultationForm()

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/faire_consultation.html', {
        'form': form,
        'signes': signes,
        'patient': patient,
        'prestations': prestations_labo ,
        'fonction' : fonction 
    })

# 20 
# ==============================================================================================
# dossier du patient pour voir toutes ces consultations
# ==============================================================================================
@login_required()
def dossier_archive_patient(request, patient_id):
    # Récupération du patient
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Récupération de toutes les consultations liées à ce patient
    # On utilise prefetch_related pour optimiser la base de données
    consultations = Consultation.objects.filter(patient=patient).order_by('-date_consultation').prefetch_related('examens_prescrits__prestation')

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/dossier_archive_patient.html', {
        'patient': patient,
        'consultations': consultations,
        'fonction':fonction 
    })

# 21 
# ==============================================================================================
# liste de patient consulte
# ==============================================================================================
@login_required()
def liste_patients_consultes(request):
    # On récupère toutes les consultations, classées par la plus récente
    consultations = Consultation.objects.all().order_by('-date_consultation').select_related('patient', 'medecin')
    
    # Optionnel : Ajouter une recherche par nom
    query = request.GET.get('search')
    if query:
        consultations = consultations.filter(patient__noms__icontains=query)

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/liste_patients_consultes.html', {
        'consultations': consultations ,
        'fonction' : fonction 
    })

# 22
# ===============================================================================================
# paiement d'examen du patient 
# ===============================================================================================
@login_required()
@transaction.atomic
def payer_examen(request, patient_id):
    # 1. Contexte et Sécurité
    patient = get_object_or_404(Patient, id=patient_id)
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None
    
    # 2. On récupère les examens non encore TOTALEMENT payés
    # On trie par ID pour payer les plus anciens en premier
    examens_prescrits = ExamenPrescrit.objects.filter(
        consultation__patient=patient, 
        paye=False
    ).select_related('prestation').order_by('id')
    
    # 3. Calcul du total restant à payer sur tous ces examens
    total_du_cdf = sum(Decimal(str(ex.prix_total)) for ex in examens_prescrits)

    # 4. Gestion du Taux
    config = ConfigurationHopital.objects.first()
    taux_actuel = Decimal(str(config.taux_usd_en_cdf)) if config else Decimal("2500.0")

    if request.method == 'POST':
        montant_saisi = request.POST.get('montant_physique')
        devise = request.POST.get('devise')

        if montant_saisi:
            try:
                montant_decimal = Decimal(str(montant_saisi))
                # Conversion en CDF pour la logique de calcul
                argent_disponible_cdf = (montant_decimal * taux_actuel) if devise == 'USD' else montant_decimal

                # --- VALIDATIONS ---
                if argent_disponible_cdf > total_du_cdf:
                    messages.error(request, f"Erreur : Le montant ({int(argent_disponible_cdf)} FC) dépasse la dette totale ({int(total_du_cdf)} FC).")
                elif argent_disponible_cdf <= 0:
                    messages.error(request, "Veuillez saisir un montant valide.")
                else:
                    # --- LOGIQUE DE DISTRIBUTION (L'argent coule d'examen en examen) ---
                    reste_a_distribuer = argent_disponible_cdf
                    examens_soldes = 0

                    for examen in examens_prescrits:
                        if reste_a_distribuer <= 0:
                            break

                        # On récupère ou crée la facture liée à cet examen précis
                        facture, created = Facture.objects.get_or_create(
                            patient=patient,
                            prestation=examen.prestation,
                            # Ajoute ici un champ date ou consultation si nécessaire pour l'unicité
                        )

                        # Calcul de ce qu'il reste à payer sur CET examen précis
                        # (On déduit ce qui a déjà été payé avant sur cette facture)
                        deja_paye = sum(p.montant_physique * (taux_actuel if p.devise == 'USD' else 1) for p in facture.paiements.all())
                        du_sur_cet_examen = Decimal(str(examen.prix_total)) - deja_paye

                        # On prend le minimum entre ce qu'on a et ce qu'on doit
                        versement_pour_cet_ex_cdf = min(reste_a_distribuer, du_sur_cet_examen)

                        if versement_pour_cet_ex_cdf > 0:
                            # Calcul de la part physique selon la devise de saisie
                            part_physique = versement_pour_cet_ex_cdf / taux_actuel if devise == 'USD' else versement_pour_cet_ex_cdf

                            # Enregistrement du paiement
                            Paiement.objects.create(
                                facture=facture,
                                montant_physique=part_physique,
                                devise=devise
                            )

                            # Si l'examen est maintenant totalement payé
                            if (deja_paye + versement_pour_cet_ex_cdf) >= Decimal(str(examen.prix_total)):
                                examen.paye = True
                                examen.save()
                                examens_soldes += 1

                            # On soustrait ce qu'on vient de donner
                            reste_a_distribuer -= versement_pour_cet_ex_cdf

                    messages.success(request, f"Paiement de {int(argent_disponible_cdf)} FC enregistré. {examens_soldes} examen(s) soldé(s).")
                    return redirect('patientRead')

            except Exception as e:
                messages.error(request, f"Erreur technique : {str(e)}")

    return render(request, 'back-end/encaisser_examen.html', {
        'patient': patient,
        'examens': examens_prescrits,
        'total_cdf': total_du_cdf,
        'taux': taux_actuel,
        'profil': profil,
        'fonction': fonction,
    })

# 23 
# =============================================================================================
# liste des examens a faire cote  labo
# =============================================================================================
@login_required
def liste_examens_labo(request):
    """Affiche uniquement les examens payés qui attendent une analyse"""
    # On filtre : paye=True ET termine=False
    examens_a_faire = ExamenPrescrit.objects.filter(
        paye=True, 
        termine=False
    ).select_related('consultation__patient', 'prestation').order_by('-date_prescription')
    

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/labo_liste.html', {
        'examens': examens_a_faire , 
        'fonction' : fonction 
    })

# 24 
# ============================================================================================
#  """Permet au laborantin de saisir ses conclusions et valider l'examen"""
# ============================================================================================
@login_required
def saisir_resultat_labo(request, examen_id):
    
    examen = get_object_or_404(ExamenPrescrit, id=examen_id)
    
    if request.method == 'POST':
        resultat = request.POST.get('resultat_labo')
        
        if resultat:
            # On met à jour l'objet ExamenPrescrit
            examen.resultat_labo = resultat
            examen.termine = True
            examen.date_analyse = timezone.now()
            examen.laborantin = request.user
            examen.save()
            
            messages.success(request, f"Résultats enregistrés pour {examen.prestation.libelle}.")
            return redirect('liste_examens_labo')
        else:
            messages.error(request, "Le champ résultat ne peut pas être vide.")

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/saisir_resultat.html', {'examen': examen , 'fonction': fonction})

# 25 
# ======================================================================================================
# une traçabilité totale
# =======================================================================================================
@login_required
def historique_paiements(request):
    # On récupère tous les paiements avec les infos de la facture et du patient
    # pour éviter de ralentir la base de données (select_related)
    tous_les_paiements = Paiement.objects.all().select_related(
        'facture__patient', 
        'facture__prestation'
    ).order_by('-date_paiement')

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/compta_paiements.html', {
        'paiements': tous_les_paiements ,
        'fonction': fonction
    })

# 26
# ========================================================================================================= 
# partie finance 
# =========================================================================================================
@login_required
def tableau_bord_finance(request):
    aujourdhui = timezone.now()
    
    # --- ENTRÉES (Paiements patients) ---
    entrees_usd = Paiement.objects.filter(devise='USD').aggregate(total=Sum('montant_physique'))['total'] or 0
    entrees_cdf = Paiement.objects.filter(devise='CDF').aggregate(total=Sum('montant_physique'))['total'] or 0
    total_entrees_en_cdf = Paiement.objects.aggregate(total=Sum('montant_comptable_cdf'))['total'] or 0

    # --- DÉPENSES (Sorties d'argent) ---
    sorties_usd = Depense.objects.filter(devise='USD').aggregate(total=Sum('montant'))['total'] or 0
    sorties_cdf = Depense.objects.filter(devise='CDF').aggregate(total=Sum('montant'))['total'] or 0
    total_sorties_en_cdf = Depense.objects.aggregate(total=Sum('valeur_cdf'))['total'] or 0

    # --- SOLDE NET (Réel en caisse) ---
    solde_usd = entrees_usd - sorties_usd
    solde_cdf = entrees_cdf - sorties_cdf
    solde_general_cdf = total_entrees_en_cdf - total_sorties_en_cdf

    # --- STATS PAR PÉRIODES ---
    entree_jour = Paiement.objects.filter(date_paiement__date=aujourdhui.date()).aggregate(total=Sum('montant_comptable_cdf'))['total'] or 0
    
    debut_semaine = aujourdhui.date() - timedelta(days=aujourdhui.weekday())
    entree_semaine = Paiement.objects.filter(date_paiement__date__gte=debut_semaine).aggregate(total=Sum('montant_comptable_cdf'))['total'] or 0
    
    entree_mois = Paiement.objects.filter(date_paiement__month=aujourdhui.month, date_paiement__year=aujourdhui.year).aggregate(total=Sum('montant_comptable_cdf'))['total'] or 0
    entree_annee = Paiement.objects.filter(date_paiement__year=aujourdhui.year).aggregate(total=Sum('montant_comptable_cdf'))['total'] or 0

    # --- TOP PRESTATIONS (Correction définitive de la jointure) ---
    # On groupe par le libellé de la prestation à travers la facture liée au paiement
    stats_prestations = Paiement.objects.values(
        'facture__prestation__libelle'
    ).annotate(
        total_genere=Sum('montant_comptable_cdf'),
        nombre_actes=Count('id')
    ).filter(total_genere__gt=0).order_by('-total_genere')

    # --- GESTION DU PROFIL ---
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    context = {
        'solde_usd': solde_usd,
        'solde_cdf': solde_cdf,
        'solde_general_cdf': solde_general_cdf,
        'total_entrees': total_entrees_en_cdf,
        'total_sorties': total_sorties_en_cdf,
        'entree_jour': entree_jour,
        'entree_semaine': entree_semaine,
        'entree_mois': entree_mois,
        'entree_annee': entree_annee,
        'stats_prestations': stats_prestations,
        'fonction': fonction,
    }
    return render(request, 'back-end/finance_dashboard.html', context)

# 27 
# =========================================================================================
# geston de depense
# =========================================================================================
@login_required()
def gestion_depenses(request):
    # 1. Calcul du solde actuel (Entrées - Sorties) en CDF
    total_entrees = Paiement.objects.aggregate(total=Sum('montant_comptable_cdf'))['total'] or 0
    total_sorties = Depense.objects.aggregate(total=Sum('valeur_cdf'))['total'] or 0
    solde_disponible = total_entrees - total_sorties

    if request.method == 'POST':
        form = DepenseForm(request.POST)
        if form.is_valid():
            # On ne sauvegarde pas encore, on récupère l'objet pour tester son montant
            instance = form.save(commit=False)
            
            # Récupération du taux pour la conversion temporaire si c'est du USD
            montant_a_depenser_cdf = instance.montant
            if instance.devise == 'USD':
                config = ConfigurationHopital.objects.first()
                taux = config.taux_usd_en_cdf if config else 2500 # Valeur de secours
                montant_a_depenser_cdf = instance.montant * taux

            # --- VÉRIFICATION DU SOLDE ---
            if montant_a_depenser_cdf > solde_disponible:
                messages.error(request, f"Opération refusée : Solde insuffisant. (Disponible: {solde_disponible:.0f} FC)")
            else:
                instance.save()
                messages.success(request, "Dépense enregistrée avec succès.")
                return redirect('gestion_depenses')
    else:
        form = DepenseForm()

    # Reste de ta logique
    depenses = Depense.objects.all().order_by('-date_depense')

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    return render(request, 'back-end/depenses.html', {
        'depenses': depenses,
        'form': form,
        'fonction': fonction,
        'solde_disponible': solde_disponible ,

    })

# 28 
# =======================================================================================
# gestion de chambre 
# =======================================================================================
@login_required
def ajouter_chambre(request):
    if request.method == "POST":
        numero = request.POST.get('numero')
        type_chambre = request.POST.get('type_chambre')
        prix = request.POST.get('prix')

        # Vérification si le numéro de chambre existe déjà
        if Chambre.objects.filter(numero=numero).exists():
            messages.error(request, f"Erreur : La chambre {numero} existe déjà dans le système.")
            return render(request, 'back-end/ajouter_chambre.html')

        try:
            Chambre.objects.create(
                numero=numero,
                type_chambre=type_chambre,
                prix_journalier=prix
            )
            messages.success(request, f"La Chambre {numero} a été enregistrée avec succès.")
            return redirect('gestion_chambres')
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {e}")

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None
            
    return render(request, 'back-end/ajouter_chambre.html', {'fonction':fonction})

# 29
# ======================================================================================
# ajoute lit
# =======================================================================================
@login_required
def ajouter_lit(request):
    chambres = Chambre.objects.all()
    
    if request.method == "POST":
        chambre_id = request.POST.get('chambre')
        nom_lit = request.POST.get('nom_lit')
        
        chambre = Chambre.objects.get(id=chambre_id)
        
        # Création du lit
        Lit.objects.create(
            chambre=chambre,
            nom_lit=nom_lit
        )
        messages.success(request, f"Le lit {nom_lit} a été ajouté à la chambre {chambre.numero}.")
        return redirect('gestion_chambres')

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    return render(request, 'back-end/ajouter_lit.html', {'chambres': chambres , 'fonction':fonction})

# 30 
# =================================================================================================
# gestion de chambre 
# ==================================================================================================
@login_required
def gestion_chambres(request):
    """ Cette vue manquait ! Elle affiche l'état des chambres et des lits """
    # On récupère tous les lits pour les stats
    lits = Lit.objects.all()
    
    # On récupère uniquement les occupations en cours (pour le tableau)
    occupations_actives = OccupationLit.objects.filter(
        date_sortie__isnull=True
    ).select_related('patient', 'lit__chambre')

    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    context = {
        'lits': lits,
        'occupations_actives': occupations_actives,
        'fonction' : fonction , 
    }
    

    return render(request, 'back-end/gestion_chambres.html', context)

# 31 
# ===================================================================================================
# liste de chambre 
# ===================================================================================================
@login_required
def liste_chambres(request):
    # On récupère les chambres ET leurs lits en une seule requête optimisée
    chambres = Chambre.objects.prefetch_related('lits').all().order_by('-id')

    # Récupération du profil avec sa fonction
    profil = Profil.objects.select_related('fonction').filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None
    
    context = {
        'chambres': chambres, 
        'fonction': fonction
    }
    
    return render(request, 'back-end/liste_chambres.html', context)

# 31 
# ======================================================================================================
# liste des lits
# ======================================================================================================
@login_required
def liste_lits(request):
    # Récupérer tous les lits et leurs chambres associées
    lits = Lit.objects.select_related('chambre').all().order_by('chambre__numero', 'nom_lit')
    
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    return render(request, 'back-end/liste_lits.html', {
        'lits': lits,
        'fonction': fonction
    })

# 32
# =====================================================================================================
# resultat du labo 
# ======================================================================================================
@login_required()
def examens_termines_medecin(request):
    # 1. On cherche les CONSULTATIONS du médecin connecté 
    # qui ont au moins un examen terminé (termine=True)
    # .distinct() évite d'avoir la même consultation 3 fois si elle a 3 examens.
    consultations_avec_resultats = Consultation.objects.filter(
        medecin=request.user,
        examens_prescrits__termine=True
    ).prefetch_related('examens_prescrits', 'patient').distinct().order_by('-date_consultation')

    # 2. Récupération du profil pour la sidebar
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    return render(request, 'back-end/medecin_resultats_labo.html', {
        'consultations': consultations_avec_resultats,
        'fonction': fonction,
        'profil_connecte': profil_connecte
    })
# 33
# =======================================================================================================
# ordonnance 
# =======================================================================================================
@login_required
def rediger_ordonnance(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    patient = consultation.patient
    
    # 1. Récupération des médicaments disponibles
    produits_stock = Medicament.objects.filter(quantite_stock_pieces__gt=0).order_by('designation')
    
    examens_faits = ExamenPrescrit.objects.filter(
        consultation=consultation, termine=True
    ).select_related('prestation')

    if request.method == "POST":
        medics_ids = request.POST.getlist('produit_id[]')
        qtes_demandees = request.POST.getlist('quantite_prescrite[]')
        posologie_globale = request.POST.get('posologie', '')

        if not medics_ids:
            messages.error(request, "Veuillez ajouter au moins un médicament.")
        else:
            erreurs = []
            lignes_a_creer = []

            # 2. Vérification technique des stocks
            for m_id, q_voulue in zip(medics_ids, qtes_demandees):
                try:
                    if not q_voulue or int(q_voulue) <= 0:
                        continue
                        
                    medoc = Medicament.objects.get(id=m_id)
                    q_voulue = int(q_voulue)

                    if medoc.quantite_stock_pieces < q_voulue:
                        erreurs.append(
                            f"Stock insuffisant pour {medoc.designation}. "
                            f"Disponible: {medoc.quantite_stock_pieces}, Demandé: {q_voulue}."
                        )
                    else:
                        lignes_a_creer.append({
                            'objet_medoc': medoc,
                            'quantite': q_voulue
                        })
                except (Medicament.DoesNotExist, ValueError):
                    continue

            if erreurs:
                for err in erreurs:
                    messages.error(request, err)
            else:
                try:
                    # 3. SAUVEGARDE ATOMIQUE (Tout ou rien)
                    with transaction.atomic():
                        # A. Création de l'objet Ordonnance principal
                        # On garde contenu_prescription pour l'historique texte
                        description_texte = "Détail des lignes :\n" + "\n".join([
                            f"- {l['objet_medoc'].designation}: {l['quantite']}" for l in lignes_a_creer
                        ])
                        
                        ordonnance = Ordonnance.objects.create(
                            consultation=consultation,
                            medecin=request.user,
                            contenu_prescription=description_texte,
                            instructions_posologie=posologie_globale
                        )

                        # B. Création des LigneOrdonnance pour le suivi CAISSE/PHARMACIE
                        for item in lignes_a_creer:
                            LigneOrdonnance.objects.create(
                                ordonnance=ordonnance,
                                medicament=item['objet_medoc'],
                                quantite_prescrite=item['quantite'],
                                quantite_payee=0,    # Initialement 0
                                quantite_delivree=0  # Initialement 0
                            )

                        messages.success(request, f"Ordonnance n°{ordonnance.id} enregistrée. Le patient peut passer à la caisse.")
                        return redirect('resultats_labo_medecin')
                
                except Exception as e:
                    messages.error(request, f"Erreur technique lors de la sauvegarde : {e}")

    # Gestion du profil pour la sidebar
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None
    
    context = {
        'consultation': consultation,
        'patient': patient,
        'examens': examens_faits,
        'produits_stock': produits_stock,
        'fonction': fonction,
    }
    return render(request, 'back-end/rediger_ordonnance.html', context)
    


# 34 
# =====================================================================================================
# liste des ordonnances
# ======================================================================================================
@login_required
def liste_ordonnances_infirmier(request):
    # On récupère les ordonnances qui n'ont pas encore été délivrées/traitées
    # ordonnees par les plus récentes
    ordonnances = Ordonnance.objects.filter(est_delivré=False).select_related(
        'consultation__patient', 
        'medecin'
    )
    
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    context = {
        'ordonnances': ordonnances,
        'fonction': fonction,
        'title': "Plan de Traitement - Infirmier"
    }
    return render(request, 'back-end/infirmier_liste_ordonnances.html', context)

# 35 
# =====================================================================================================
# detail ordonnance 
# ======================================================================================================
@login_required()
def detail_ordonnance_traitement(request, ordonnance_id):
    """
    Vue permettant à l'infirmier de consulter une ordonnance 
    et de marquer le traitement comme effectué (délivré).
    """
    # 1. Récupération de l'ordonnance avec les détails du patient
    ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
    
    # 2. Gestion de la validation (Action de l'infirmier)
    if request.method == "POST":
        # On passe le statut à True pour indiquer que le soin est fait
        ordonnance.est_delivré = True
        ordonnance.save()
        
        # Message de confirmation pour l'utilisateur
        messages.success(request, f"Le traitement pour {ordonnance.consultation.patient.noms} a été marqué comme délivré.")
        
        # Redirection vers la liste globale des attentes
        return redirect('liste_ordonnances_infirmier')

    # 3. Préparation du contexte pour l'affichage (GET)
    # On récupère le profil pour que le menu sidebar s'affiche correctement
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None
    
    context = {
        'ordonnance': ordonnance,
        'fonction': fonction,
        'title': f"Détail Traitement - {ordonnance.consultation.patient.noms}"
    }

    return render(request, 'back-end/infirmier_detail_ordonnance.html', context)

# 36 
# ========================================================================================
# ajoute stocker partie pharmacie
# =========================================================================================
@login_required
def ajouter_stock(request):
    produits = Medicament.objects.all().order_by('designation')

    if request.method == "POST":
        medicament_id = request.POST.get('medicament_id')
        nb_cartons = request.POST.get('nb_cartons')
        prix_achat = request.POST.get('prix_achat_carton')
        fournisseur = request.POST.get('fournisseur')

        # 1. Vérification de base des champs
        if not all([medicament_id, nb_cartons, prix_achat]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'back-end/ajouter_stock.html', {'produits': produits})

        try:
            med = Medicament.objects.get(id=medicament_id)
            nb_cartons = int(nb_cartons)
            prix_achat = float(prix_achat)

            # 2. PROTECTION ANTI-DOUBLON (Sécurité 5 minutes)
            # On vérifie si un bon identique a été créé pour ce produit dans les 5 dernières minutes
            temps_limite = timezone.now() - timedelta(minutes=5)
            doublon = BonEntree.objects.filter(
                medicament=med,
                nb_cartons_recus=nb_cartons,
                prix_achat_carton=prix_achat,
                date_reception__gte=temps_limite
            ).exists()

            if doublon:
                messages.warning(request, f"Attention : Un bon identique pour {med.designation} a déjà été enregistré il y a quelques instants.")
                return redirect('liste_stock')

            # 3. CRÉATION DU BON
            bon = BonEntree.objects.create(
                medicament=med,
                nb_cartons_recus=nb_cartons,
                prix_achat_carton=prix_achat,
                fournisseur=fournisseur
            )

            # 4. LOG DE L'OPÉRATION
            LogPharmacie.objects.create(
                utilisateur=request.user,
                action='ENTREE',
                details=f"Achat de {nb_cartons} cartons de {med.designation} chez {fournisseur}."
            )

            messages.success(request, f"Stock de {med.designation} mis à jour (+{nb_cartons} cartons).")
            return redirect('liste_stock')

        except Medicament.DoesNotExist:
            messages.error(request, "Médicament introuvable.")
        except ValueError:
            messages.error(request, "Veuillez saisir des nombres valides pour la quantité et le prix.")
        except Exception as e:
            messages.error(request, f"Erreur critique : {e}")

    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    return render(request, 'back-end/ajouter_stock.html', {'produits': produits , 'fonction':fonction})






#37
# =========================================================================================
# ajouter medicament
# =========================================================================================
@login_required
def ajouter_medicament(request):
    if request.method == "POST":
        designation = request.POST.get('designation')
        forme = request.POST.get('forme')
        dosage = request.POST.get('dosage')
        
        pieces_brutes = request.POST.get('pieces_par_carton')
        prix_detail_brut = request.POST.get('prix_vente_detail')
        prix_gros_brut = request.POST.get('prix_vente_gros')
        seuil_brut = request.POST.get('seuil_alerte')

        # --- VÉRIFICATION DE DOUBLON ---
        # On vérifie si un médicament avec le même nom, forme ET dosage existe déjà
        existe_deja = Medicament.objects.filter(
            designation__iexact=designation, 
            forme__iexact=forme, 
            dosage__iexact=dosage
        ).exists()

        if existe_deja:
            messages.warning(request, f"Le médicament '{designation} ({forme} {dosage})' existe déjà dans le système.")
            # On reste sur la page pour permettre de corriger
        else:
            try:
                Medicament.objects.create(
                    designation=designation,
                    forme=forme,
                    dosage=dosage,
                    pieces_par_carton=int(pieces_brutes) if pieces_brutes else 1,
                    prix_vente_detail=float(prix_detail_brut) if prix_detail_brut else 0.0,
                    prix_vente_gros=float(prix_gros_brut) if prix_gros_brut else 0.0,
                    seuil_alerte=int(seuil_brut) if seuil_brut else 5,
                    quantite_stock_pieces=0
                )
                messages.success(request, f"Le médicament {designation} a été créé avec succès.")
                return redirect('liste_stock')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {e}")

    # Logique de profil habituelle
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    return render(request, 'back-end/ajouter_medicament.html', {'fonction': fonction})

# 37 
# ========================================================================================
#  liste de stock
# ========================================================================================
@login_required()
def liste_stock(request):
    # On récupère tous les médicaments
    stocks = Medicament.objects.all().order_by('designation')
    
    # Logique pour compter les alertes basée sur le seuil de chaque produit
    # On crée une liste des IDs des médicaments en alerte
    alertes_ids = [s.id for s in stocks if s.est_en_alerte]
    alertes_count = len(alertes_ids)

    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    context = {
        'stocks': stocks,
        'total_articles': stocks.count(),
        'alertes_stock': alertes_count,
        'title': "Inventaire de la Pharmacie",
        'fonction': fonction
    }
    return render(request, 'back-end/liste_stock.html', context)
# 38
# =============================================================================================
# inventaire global meme action que liste stock
# =============================================================================================
@login_required
def inventaire_global(request):
    stocks = Medicament.objects.all()
    total_articles = stocks.count()
    alertes_stock = sum(1 for med in stocks if med.est_en_alerte)
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None
    
    return render(request, 'back-end/inventaire.html', {
        'stocks': stocks,
        'total_articles': total_articles,
        'alertes_stock': alertes_stock,
        'fonction': fonction 
    })

# 39
# =====================================================================================================
# medicament details
# =====================================================================================================
@login_required
def medicament_details(request, pk):
    # On récupère le médicament ou on affiche une erreur 404 s'il n'existe pas
    medicament = get_object_or_404(Medicament, pk=pk)
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    return render(request, 'back-end/details_medicament.html', {'medicament': medicament, 'fonction':fonction})

# 40
# =====================================================================================================
# medicament historique
# =====================================================================================================
@login_required
def medicament_historique(request, pk):
    medicament = get_object_or_404(Medicament, pk=pk)
    
    # On récupère les entrées (achats) et les sorties (ventes) pour ce produit
    entrees = BonEntree.objects.filter(medicament=medicament).order_by('-date_reception')
    sorties = LigneVente.objects.filter(medicament=medicament).order_by('-vente__date_vente')

    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None
    
    context = {
        'medicament': medicament,
        'entrees': entrees,
        'sorties': sorties,
        'fonction' : fonction 
    }
    return render(request, 'back-end/historique_medicament.html', context)

# 41
# ====================================================================================================
# dashboard pharmacie gestion finance cote pharmacie
# ====================================================================================================
@login_required()
def dashboard_pharmacie(request):
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil_connecte.fonction.fonction if profil_connecte and profil_connecte.fonction else None

    # 1. Récupération des données de base
    stocks = Medicament.objects.all()
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2500
    
    # 2. Ventes du jour (Correction ici)
    # timezone.now().date() est plus fiable que datetime.date.today()
    aujourdhui = timezone.now().date() 
    
    ventes_du_jour = VentePharmacie.objects.filter(
        date_vente__date=aujourdhui, 
        statut='VALIDE'
    )

    # 3. Calculs financiers
    ca_jour_cdf = ventes_du_jour.aggregate(total=Sum('total_cdf'))['total'] or 0
    
    # Sécurité pour éviter la division par zéro si le taux n'est pas configuré
    try:
        ca_jour_usd = float(ca_jour_cdf) / float(taux)
    except (ZeroDivisionError, TypeError):
        ca_jour_usd = 0

    # Valeur du stock
    valeur_stock_cdf = stocks.aggregate(
        total=Sum(F('quantite_stock_pieces') * F('prix_achat_unitaire_moyen'))
    )['total'] or 0
    
    try:
        valeur_stock_usd = float(valeur_stock_cdf) / float(taux)
    except (ZeroDivisionError, TypeError):
        valeur_stock_usd = 0

    context = {
        'total_articles': stocks.count(),
        'alertes_stock': sum(1 for med in stocks if med.est_en_alerte),
        'valeur_stock_cdf': valeur_stock_cdf,
        'valeur_stock_usd': valeur_stock_usd,
        'ca_jour_cdf': ca_jour_cdf,
        'ca_jour_usd': ca_jour_usd,
        'taux': taux,
        'ventes_recentes': ventes_du_jour.order_by('-date_vente')[:5],
        'fonction': fonction 
    }
    return render(request, 'back-end/dashboard.html', context)

# 42
# ==============================================================================================
# nouvelle vente 
# ==============================================================================================
@login_required
@transaction.atomic
def effectuer_vente(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            panier = data.get('panier')
            patient_id = data.get('patient_id')
            
            if not panier:
                return JsonResponse({'status': 'error', 'message': 'Panier vide'})

            # 1. Vérification de la configuration et de la prestation
            config = ConfigurationHopital.objects.first()
            prestation_pharma = Prestation.objects.filter(libelle__icontains="PHARMACIE").first()
            
            if not config or not prestation_pharma:
                return JsonResponse({'status': 'error', 'message': 'Configuration ou Prestation PHARMACIE manquante.'})

            # 2. Identification du patient (si fourni)
            patient = None
            if patient_id:
                patient = Patient.objects.get(id=patient_id)

            # 3. Création de la Vente
            nouvelle_vente = VentePharmacie.objects.create(
                vendeur=request.user,
                patient=patient,
                total_cdf=0 # Sera mis à jour après
            )

            total_global = 0
            for item in panier:
                med = Medicament.objects.select_for_update().get(id=item['id'])
                qte = int(item['quantite'])
                prix_u = Decimal(str(item['prix']))
                
                # Vérification stock de sécurité
                if med.quantite_stock_pieces < qte:
                    raise ValueError(f"Stock insuffisant pour {med.designation}")

                # Création ligne
                LigneVente.objects.create(
                    vente=nouvelle_vente,
                    medicament=med,
                    quantite=qte,
                    prix_unitaire_applique=prix_u
                )

                # Mise à jour stock
                med.quantite_stock_pieces -= qte
                med.save()
                total_global += (prix_u * qte)

            # Mise à jour du total final
            nouvelle_vente.total_cdf = total_global
            nouvelle_vente.save()

            # 4. Création de la Facture (Automatique via ta logique métier)
            # Note: Si c'est un patient, ton modèle Facture vérifiera la fiche valide
            try:
                facture = Facture.objects.create(
                    patient=patient if patient else Patient.objects.first(), # Ajuste selon ta gestion "Comptoir"
                    prestation=prestation_pharma,
                    vente_pharmacie=nouvelle_vente,
                    prix_fixe_cdf=total_global
                )

                # 5. Enregistrement du Paiement
                Paiement.objects.create(
                    facture=facture,
                    montant_physique=total_global,
                    devise='CDF'
                )
            except ValidationError as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

            return JsonResponse({
                'status': 'success', 
                'message': 'Vente et facturation terminées',
                'vente_id': nouvelle_vente.id
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Partie GET
    medicaments = Medicament.objects.filter(quantite_stock_pieces__gt=0).order_by('designation')
    patients = Patient.objects.all().order_by('noms')
    return render(request, 'back-end/nouvelle_vente.html', {
        'medicaments': medicaments,
        'patients': patients
    })

# 43 
# ===========================================================================================================
# historique vente
# ===========================================================================================================
@login_required
def historique_ventes(request):
    # Récupération de toutes les ventes validées, triées par date (récente en haut)
    ventes = VentePharmacie.objects.filter(statut='VALIDE').order_by('-date_vente')
    
    # Récupération du taux pour conversion globale si besoin
    config = ConfigurationHopital.objects.first()
    taux = config.taux_usd_en_cdf if config else 2500
    
    context = {
        'ventes': ventes,
        'taux': taux,
    }
    return render(request, 'back-end/historique_ventes.html', context)

# 44
# ===========================================================================================================
# annuler vente
# ===========================================================================================================
@login_required
def annuler_vente(request, vente_id):
    vente = get_object_or_404(VentePharmacie, id=vente_id)
    
    if vente.statut == 'ANNULE':
        messages.warning(request, "Cette vente est déjà annulée.")
        return redirect('historique_ventes')

    with transaction.atomic():
        # 1. Remettre les produits en stock
        for ligne in vente.lignes.all():
            med = ligne.medicament
            med.quantite_stock_pieces += ligne.quantite
            med.save()
        
        # 2. Changer le statut
        vente.statut = 'ANNULE'
        vente.save()
        
        # 3. Logger l'action
        LogPharmacie.objects.create(
            utilisateur=request.user,
            action='ANNULATION',
            details=f"Annulation de la facture #{vente.id} d'un montant de {vente.total_cdf} CDF"
        )
        
    messages.success(request, f"La vente #{vente.id} a été annulée et le stock mis à jour.")
    return redirect('historique_ventes')


# 45 
# ===========================================================================================================
# genere facture vente
# ===========================================================================================================
@login_required
def generer_facture_pdf(request, vente_id):
    vente = get_object_or_404(VentePharmacie, id=vente_id)
    return render(request, 'back-end/facture_format_ticket.html', {'vente': vente})

# 46
# =============================================================================================================
# liste des ordonnance 
# =============================================================================================================
@login_required
def liste_ordonnances(request):
    # 1. Récupération du profil et de la fonction
    profil_connecte = Profil.objects.filter(userProfil=request.user).first()
    nom_fonction = profil_connecte.fonction.fonction.upper() if profil_connecte and profil_connecte.fonction else ""

    # 2. Base de la requête : On prend tout, trié par date
    queryset = Ordonnance.objects.select_related(
        'consultation__patient', 
        'medecin'
    ).order_by('-date_creation')

    # 3. Logique d'affichage par rôle
    if "INFIRMIER" in nom_fonction:
        # L'infirmier se concentre sur les tâches urgentes (non délivrées)
        ordonnances = queryset.filter(est_delivré=False)
        page_title = "Plan de Soins - Ordonnances à Traiter"
    
    elif "MEDECIN" in nom_fonction:
        # Le médecin voit TOUT pour le suivi clinique, confrères inclus
        ordonnances = queryset.all()
        page_title = "Registre des Prescriptions Médicales"
    
    else:
        # Pharmacie ou Admin : tout voir par défaut
        ordonnances = queryset.all()
        page_title = "Gestion des Ordonnances"

    context = {
        'ordonnances': ordonnances,
        'fonction': nom_fonction,
        'user_actuel': request.user, # Pour mettre en avant ses propres ordonnances dans le HTML
        'title': page_title
    }
    
    return render(request, 'back-end/liste_ordonnances_generale.html', context)

# 47
# ================================================================================================
# detail ordonnance
# ================================================================================================
@login_required
def ordonnance_details(request, ordonnance_id):
    # On récupère l'ordonnance ou erreur 404
    ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
    
    # On récupère toutes les lignes (médicaments) liées à cette ordonnance
    # 'lignes' est le related_name que tu as normalement dans ton modèle LigneOrdonnance
    lignes = ordonnance.lignes.all() 

    context = {
        'ordonnance': ordonnance,
        'lignes': lignes,
        'title': f"Détails Ordonnance #{ordonnance.id}"
    }
    return render(request, 'back-end/ordonnance_details.html', context)

# 48
# ===============================================================================================
# delivre orodnnance 
# ===============================================================================================
@login_required
def delivrer_ordonnance(request, ordonnance_id):
    ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
    
    if request.method == "POST":
        # On passe le statut à True
        ordonnance.est_delivré = True
        ordonnance.save()
        
        # Optionnel : Tu peux ici ajouter une logique pour déduire 
        # automatiquement les quantités du stock si ce n'est pas déjà fait via les signaux.
        
        messages.success(request, f"L'ordonnance #{ordonnance.id} a été marquée comme délivrée avec succès.")
        return redirect('liste_ordonnances')

    # Si on y accède par erreur en GET, on redirige vers la liste
    return redirect('liste_ordonnances')

# 49 
# =====================================================================
# payer ordonnance 
# =======================================================================
@login_required
def payer_ordonnance(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # On cherche l'ordonnance non payée
    ordonnance = Ordonnance.objects.filter(
        consultation__patient=patient, 
        est_paye=False 
    ).order_by('-date_creation').first()

    if not ordonnance:
        messages.warning(request, f"Aucune ordonnance en attente de paiement pour {patient.noms}.")
        return redirect('patientRead') # <-- CORRIGÉ ICI

    if request.method == 'POST':
        ordonnance.est_paye = True
        ordonnance.save()
        
        messages.success(request, f"Paiement validé pour l'ordonnance #{ordonnance.id}.")
        return redirect('patientRead') # <-- CORRIGÉ ICI

    context = {
        'patient': patient,
        'ordonnance': ordonnance,
        'title': "Paiement de l'Ordonnance"
    }
    
    return render(request, 'back-end/payer_ordonnance.html', context)

# 50
# ==========================================================================================================
# supprimer profil
# ==========================================================================================================
@login_required
def supprimer_profil(request, profil_id):
    # On récupère le profil ou on renvoie une erreur 404
    profil = get_object_or_404(Profil, id=profil_id)
    
    # Sécurité : Seul l'utilisateur lui-même ou un admin peut supprimer
    if request.user == profil.userProfil or request.user.is_staff:
        if request.method == 'POST':
            profil.delete()
            messages.success(request, "Le profil a été supprimé avec succès.")
            return redirect('profilRead') 
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer ce profil.")
        return redirect('ProfilRead')

    return render(request, 'back-end/confirmer_suppression.html', {'profil': profil})


# 51
# ========================================================================================================
# modifier profile
# ========================================================================================================
@login_required
def modifier_profil(request, profil_id):
    # Récupérer le profil à modifier
    profil = get_object_or_404(Profil, id=profil_id)
    
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            messages.success(request, "Le profil a été mis à jour avec succès !")
            return redirect('profilRead') # 
    else:
        # Pré-remplir le formulaire avec les données actuelles
        form = ProfilForm(instance=profil)
    
    return render(request, 'back-end/modifier_profil.html', {'form': form, 'profil': profil})


# 52 
# =========================================================================================================
# change mot de passe par d'amin c.a.d sans savoir l'ancien mot de passe
# ==========================================================================================================
@login_required
def admin_force_password(request, user_id):
    # On récupère l'utilisateur lié au profil
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # On passe l'instance de l'utilisateur au formulaire
        form = SetPasswordForm(user=user_to_edit, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le mot de passe de {user_to_edit.username} a été réinitialisé avec succès.")
            return redirect('employeRead')
    else:
        form = SetPasswordForm(user=user_to_edit)
    
    return render(request, 'back-end/changer_mdp.html', {
        'form': form, 
        'user_to_edit': user_to_edit
    })

# 53
# ==========================================================================================================
# change mot de passe par employe lui meme 
# ==========================================================================================================
@login_required
def modifier_mon_mdp(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Très important : garde la session active après le changement
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a été mis à jour avec succès !")
            return redirect('panel') 
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'back-end/mon_compte_mdp.html', {'form': form}) 

# 54
# =======================================================================================================
# ajouter materiel
# =======================================================================================================
@login_required
def ajouter_materiel(request):
    services = Service.objects.all()
    
    if request.method == 'POST':
        n_serie = request.POST.get('numero_serie')
        
        # 1. Vérification : Est-ce que ce numéro de série existe déjà ?
        if Materiel.objects.filter(numero_serie=n_serie).exists():
            messages.error(request, f"Erreur : Un matériel avec le numéro de série '{n_serie}' existe déjà dans le système.")
            # On renvoie vers le formulaire avec les données déjà saisies pour ne pas tout retaper
            return render(request, 'back-end/logistique/ajouter_materiel.html', {'services': services})

        try:
            service_id = request.POST.get('service')
            service_obj = Service.objects.get(id=service_id)
            
            Materiel.objects.create(
                nom=request.POST.get('nom'),
                marque=request.POST.get('marque'),
                modele=request.POST.get('modele'),
                numero_serie=n_serie,
                categorie=request.POST.get('categorie'),
                service_affecte=service_obj,
                date_achat=request.POST.get('date_achat') or None,
                description=request.POST.get('description')
            )
            messages.success(request, "Le matériel a été enregistré avec succès.")
            return redirect('liste_materiel')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement : {e}")

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    return render(request, 'back-end/logistique/ajouter_materiel.html', {'services': services , 'fonction': fonction})

# 55
# ====================================================================================================
# liste de materiel enregistre 
# ====================================================================================================
@login_required
def liste_materiel(request):
    # 1. On récupère tous les services avec leur matériel associé
    # prefetch_related évite de faire une requête SQL par ligne (optimisation)
    services = Service.objects.prefetch_related('materiels').all()
    
    # 2. On calcule les statistiques pour le haut de la page
    total_appareils = Materiel.objects.count()
    en_panne = Materiel.objects.filter(etat_actuel='PANNE').count()
    en_reparation = Materiel.objects.filter(etat_actuel='REPARATION').count()

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    context = {
        'services': services,
        'total_appareils': total_appareils,
        'en_panne': en_panne,
        'en_reparation': en_reparation,
        'fonction' : fonction 
    }
    
    return render(request, 'back-end/logistique/liste_materiel.html', context)

# 56
# ============================================================================================================
# signaler panne materiel
# ============================================================================================================
@login_required
def signaler_panne_materiel(request, materiel_id):
    # Récupérer le matériel concerné
    materiel = get_object_or_404(Materiel, id=materiel_id)
    
    if request.method == 'POST':
        description = request.POST.get('description_panne')
        
        if not description:
            messages.error(request, "Veuillez fournir une description du problème.")
            return render(request, 'back-end/logistique/signaler_panne.html', {'materiel': materiel})
            
        try:
            # 1. Mise à jour de l'état du matériel
            materiel.etat_actuel = 'PANNE'
            materiel.save()
            
            # 2. Création de l'entrée dans la table Maintenance
            Maintenance.objects.create(
                materiel=materiel,
                description_panne=description,
                date_signalement=timezone.now(),
                est_repare=False
            )
            
            messages.warning(request, f"La panne sur {materiel.nom} (S/N: {materiel.numero_serie}) a été signalée.")
            return redirect('liste_materiel')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {e}")


    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    return render(request, 'back-end/logistique/signaler_panne.html', {'materiel': materiel , 'fonction' : fonction})


# 57 
# ===================================================================================================================
#  materiel en panne 
# ===================================================================================================================
@login_required
def materiel_en_panne(request):
    # On filtre uniquement ce qui n'est pas fonctionnel
    # On trie par service_affecte (utilise '__nomService' si tu veux trier par nom)
    materiels_panne = Materiel.objects.filter(
        etat_actuel__in=['PANNE', 'REPARATION']
    ).order_by('service_affecte')
    
    # Statistiques pour les badges du haut
    en_panne_count = Materiel.objects.filter(etat_actuel='PANNE').count()
    en_reparation_count = Materiel.objects.filter(etat_actuel='REPARATION').count()

    # Récupération du profil pour la gestion des permissions dans le template
    profil = Profil.objects.filter(userProfil=request.user).first()
    fonction = profil.fonction.fonction if profil and profil.fonction else None

    context = {
        'materiels_panne': materiels_panne,
        'en_panne': en_panne_count,
        'en_reparation': en_reparation_count,
        'fonction': fonction 
    }
    return render(request, 'back-end/logistique/materiel_en_panne.html', context)