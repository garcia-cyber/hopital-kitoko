from django.shortcuts import render , redirect , get_object_or_404
from .forms import * 
from django.contrib.auth import authenticate , login as auth , logout 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User
from .models import *
from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum, F , Q , Count
from django.forms import inlineformset_factory
from django.db import transaction  # <--- AJOUTE CETTE LIGNE
from datetime import timedelta
from django.utils import timezone

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
    # On récupère toutes les factures
    toutes_factures = Facture.objects.select_related('patient', 'prestation').all()
    config = ConfigurationHopital.objects.first()
    taux = Decimal(str(config.taux_usd_en_cdf)) if config else Decimal("2250.0")
    
    patients_prets = []

    for f in toutes_factures:
        # Calcul du total payé pour CETTE facture
        total_paye = Decimal("0.0")
        for p in f.paiements.all():
            m_p = Decimal(str(p.montant_physique))
            if p.devise == 'USD':
                total_paye += (m_p * taux)
            else:
                total_paye += m_p
        
        # Si le reste est 0 (ou très proche de 0), on l'ajoute à la liste
        prix_total = Decimal(str(f.prestation.prix_cdf))
        if total_paye >= prix_total:
            patients_prets.append({
                'patient': f.patient,
                'prestation': f.prestation.libelle,
                'date': f.date_emission,
                'facture_id': f.id
            })
    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/infirmier_signes.html', {
        'patients_prets': patients_prets , 
        'fonction' : fonction 
    })

# 16 
# =================================================================================
# prendre le signe vitaux
# =================================================================================
@login_required()
def prendre_signes(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    aujourdhui = timezone.now().date()
    
    # On cherche s'il existe déjà un enregistrement pour ce patient aujourd'hui
    instance_existante = SignesVitaux.objects.filter(
        patient=patient, 
        date_prelevement__date=aujourdhui
    ).first()

    if request.method == "POST":
        # Si instance_existante existe, Django va MODIFIER au lieu de CRÉER
        form = SignesVitauxForm(request.POST, instance=instance_existante)
        
        if form.is_valid():
            signes = form.save(commit=False)
            signes.patient = patient
            signes.infirmier = request.user
            signes.save()
            
            if instance_existante:
                messages.success(request, f"Les signes de {patient.noms} ont été mis à jour.")
            else:
                messages.success(request, f"Les signes de {patient.noms} ont été enregistrés.")
                
            return redirect('liste_soldes')
    else:
        # Au chargement de la page (GET) :
        # Si une instance existe, le formulaire sera pré-rempli avec les anciennes valeurs
        form = SignesVitauxForm(instance=instance_existante)

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/formulaire_signes.html', {
        'form': form,
        'patient': patient,
        'est_modification': instance_existante is not None ,
        'fonction' : fonction
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
        'solde_disponible': solde_disponible  # On l'envoie au template pour l'afficher
    })