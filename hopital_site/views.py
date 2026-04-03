from django.shortcuts import render , redirect , get_object_or_404
from .forms import * 
from django.contrib.auth import authenticate , login as auth , logout 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User
from .models import *
from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum, F

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
    
    if request.method == "POST":
        facture_id = request.POST.get('facture_id')
        montant_saisi = request.POST.get('montant')
        devise = request.POST.get('devise')
        
        if facture_id and montant_saisi:
            f_obj = Facture.objects.get(id=facture_id)
            config = ConfigurationHopital.objects.first()
            
            # --- CORRECTION CRUCIALE : On force tout en Decimal ---
            # On transforme le taux en Decimal
            taux = Decimal(str(config.taux_usd_en_cdf)) if config else Decimal("2250.0")
            
            deja_paye = Decimal("0.0")
            for p in f_obj.paiements.all():
                # On force le montant du paiement en Decimal
                m_p = Decimal(str(p.montant_physique))
                if p.devise == 'USD':
                    deja_paye += (m_p * taux) # Decimal * Decimal = OK
                else:
                    deja_paye += m_p
            
            # On force le prix de la prestation en Decimal
            prix_prest = Decimal(str(f_obj.prestation.prix_cdf))
            reste_actuel = prix_prest - deja_paye
            
            # On force le nouveau montant saisi en Decimal
            nouveau_val = Decimal(str(montant_saisi))
            nouveau_en_cdf = (nouveau_val * taux) if devise == 'USD' else nouveau_val

            # Vérification du dépassement
            if nouveau_en_cdf > (reste_actuel + Decimal("0.1")):
                messages.error(request, f"Montant trop élevé ! Reste : {reste_actuel} CDF")
                return redirect('historique_patient', patient_id=patient.id)
            
            # Enregistrement
            Paiement.objects.create(
                facture=f_obj,
                montant_physique=nouveau_val,
                devise=devise
            )
            messages.success(request, "Paiement validé !")
            return redirect('historique_patient', patient_id=patient.id)

    # --- PARTIE AFFICHAGE (GET) ---
    factures = Facture.objects.filter(patient=patient).select_related('prestation').order_by('-id')
    config = ConfigurationHopital.objects.first()
    taux_aff = Decimal(str(config.taux_usd_en_cdf)) if config else Decimal("2250.0")

    for f in factures:
        ses_paiements = f.paiements.all() 
        total_verse = Decimal("0.0")
        for p in ses_paiements:
            m_p_aff = Decimal(str(p.montant_physique))
            if p.devise == 'USD':
                total_verse += (m_p_aff * taux_aff)
            else:
                total_verse += m_p_aff
        
        f.somme_payee = total_verse 
        f.montant_restant = Decimal(str(f.prestation.prix_cdf)) - total_verse
        f.liste_paiements = ses_paiements 

    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None

    return render(request, 'back-end/historique_patient.html', {
        'patient': patient, 'factures': factures, 'taux': taux_aff , 'fonction':fonction
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
    # Pour l'instant, on affiche juste une page simple ou on redirige
    return render(request, 'back-end/formulaire_signes.html', {'patient': patient})
