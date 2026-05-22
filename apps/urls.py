from django.urls import path
from .views import *
from . import views 
#
#
# 
urlpatterns =[
     # ===================================
     # page d'accueil login

     path('', home , name = "home") ,
     path('login/', login , name ='login') ,
     path('deco/', deco , name ='deco') ,
     path('dashboard/', dashboard , name="dashboard") ,
     path('reinitialiser-password/<int:user_id>/', views.force_reinitialiser_pass, name='force_pass'),
     path('modifier-utilisateur/<int:user_id>/', views.modifier_utilisateur, name='modifier_user'),
     path('reinitialiser-password/<int:user_id>/', views.force_reinitialiser_pass, name='force_pass'),


     # ================================
     # PRESTATION 
     path('prestations/', views.gestion_prestations, name='gestion_prestations'),
     path('config/taux/', views.modifier_taux, name='modifier_taux'),
     path('prestations/modifier/<int:pk>/', views.modifier_prestation, name='modifier_prestation'),

     # =================================
     # SERVICE
     path('services/', views.gestion_services, name='gestion_services'),
     path('services/modifier/<int:pk>/', views.modifier_service, name='modifier_service'),


     # employe CRUD
     #
     path('employeAdd/', employeAdd , name = 'employeAdd'),
     path('employeRead/', employeRead , name = 'employeRead') ,
     path('ajouter-fonction/<int:user_id>/', views.attribuer_fonction, name='ajouter_fonction'),
     path('employe-poste/', views.liste_employe_poste, name='liste_employe_poste'),
     path('supprimer-poste/<int:fonction_id>/', views.supprimer_poste, name='supprimer_poste'),


     # ===================================
     # PATIENT
     path('patients/enregistrement/', views.enregistrement_patient, name='enregistrement_patient'),
     path('patients/modifier/<int:pk>/', views.modifier_patient, name='modifier_patient'),
     path('patients/liste/', views.liste_patients, name='liste_patients'),

     # ====================================
     # FINANCE
     path('patient/<int:patient_id>/payer-fiche/', views.payer_fiche, name='payer_fiche'),
     path('patient/<int:patient_id>/historique/', views.historique_paiements, name='historique_paiements'),
     path('paiement/imprimer/<int:paiement_id>/', views.imprimer_recu_direct, name='imprimer_recu_direct'),
     path('finance/journal-caisse/', views.dashboard_finance, name='dashboard_finance'), 
     path('journal-caisse-depense/', views.dashboard_finance_depense, name='dashboard_finance_depense'),
     path('depense/nouvelle/', views.creer_depense, name='creer_depense'),

     # ====================================
     # INFIRMIER
     
    path('infirmerie/attente/', views.liste_attente_triage, name='liste_attente_triage'),
    path('infirmerie/saisir/<int:patient_id>/', views.saisir_signes, name='saisir_signes'),
    path('infirmerie/registre-global/', views.liste_globale_triage, name='liste_globale_triage'),
    path('infirmerie/historique/<int:patient_id>/', views.historique_signes_vitaux, name='historique_signes_vitaux'),

    # ==================================
    # MEDECIN
    path('medecin/consultations-en-attente/', views.liste_consultation_medecin, name='liste_consultation_medecin'),
    path('medecin/marquer-consulte/<int:sv_id>/', views.marquer_consulte, name='marquer_consulte'),
    path('consultation/<int:triage_id>/', views.consultation_medicale, name='consultation_medicale'),
    path('medecin/consultations/historique/', views.liste_consultations_terminees, name='liste_consultations'),
    path('consultation/<int:pk>/', views.detail_consultation, name='detail_consultation'),
    path('consultations/ordonnances-urgence/', views.liste_ordonnances_urgence, name='liste_ordonnances_urgence'),
    path('medecin/salle-d-attente/', views.liste_attente_ordonnance_view, name='liste_attente_medecin'),
    path('consultations/<int:consultation_id>/prescrire-urgence/', views.prescrire_ordonnance_urgence_rapide, name='prescrire_ordonnance_urgence_rapide'),

    # ================================
    # CAISSE
    path('caisse/file-d-attente/', views.liste_attente_caisse, name='liste_attente_caisse'),
    path('caisse/payer-examens/<int:consultation_id>/', views.encaisser_examens_prescrits, name='encaisser_examens_prescrits'),


    # ===============================
    # TECHNIQUE
    # URL pour l'espace technique (Laboratoire / Radiologie)
    path('technique/examens-a-realiser/', views.liste_examens_techniques, name='liste_examens_techniques'),
    path('technique/saisir-resultats/<int:paiement_id>/', views.saisir_resultats_examens, name='saisir_resultats_examens'),

    # ================================
    # EXAMENS
    path('examens/historique/', views.historique_examens_view, name='historique_examens'),


 ]
