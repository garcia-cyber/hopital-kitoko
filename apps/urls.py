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
     path('dossier-medical/<int:patient_id>/', views.dossier_medical_complet, name='dossier_medical_complet'),
     path('paiement/<int:patient_id>/', views.vue_paiement_carte_fidelite, name='paiement_prestation'),
     path('patients/fideles/', views.liste_patients_avec_carte, name='liste_patients_avec_carte'),
     path('patient/modifier-type/<int:patient_id>/', views.modifier_type_patient, name='modifier_type_patient'),

     # ====================================
     # FINANCE
     path('patient/<int:patient_id>/payer-fiche/', views.payer_fiche, name='payer_fiche'),
     path('patient/<int:patient_id>/historique/', views.historique_paiements, name='historique_paiements'),
     path('paiement/imprimer/<int:paiement_id>/', views.imprimer_recu_direct, name='imprimer_recu_direct'),
     path('finance/journal-caisse/', views.dashboard_finance, name='dashboard_finance'), 
     path('journal-caisse-depense/', views.dashboard_finance_depense, name='dashboard_finance_depense'),
     path('depense/nouvelle/', views.creer_depense, name='creer_depense'),
     path('patients/', views.liste_patients_urgence, name='liste_patients_urgence'),

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
    path('imprimer-consultation/<int:consultation_id>/', views.imprimer_consultation, name='imprimer_consultation'),
    path('medecin/ordonnances-delivrees/', views.liste_ordonnances_delivrees_view, name='liste_ordonnances_delivrees'),
    path('imprimer-resultat/<int:examen_id>/', views.imprimer_resultat, name='imprimer_resultat'),
    path('ordonnances/liste/', views.liste_ordonnances_prescrites_view, name='liste_ordonnances'),
    path('modifier-ordonnance/<int:ordonnance_id>/', views.modifier_ordonnance_view, name='modifier_ordonnance'),
    path('medecin/enregistrer-ordonnance/<int:triage_id>/', views.enregistrer_ordonnance_view, name='enregistrer_ordonnance'),
    path('consultation/<int:consultation_id>/ordonnance-urgence/',views.enregistrer_ordonnance_urgence,name='enregistrer_ordonnance_urgence'),
    path('consultations/<int:consultation_id>/prescrire-urgence/', views.prescrire_ordonnance_urgence_rapide, name='prescrire_ordonnance_urgence_rapide'),


    path('creer-ordonnance/<int:consultation_id>/', views.creer_ordonnance_view, name='creer_ordonnance'),
    path('medecin/liste-patients/', views.liste_patients_urgence, name='liste_patients_urgence'),
    # ================================
    # CAISSE
    path('caisse/file-d-attente/', views.liste_attente_caisse, name='liste_attente_caisse'),
    path('caisse/payer-examens/<int:consultation_id>/', views.encaisser_examens_prescrits, name='encaisser_examens_prescrits'),


    # ===============================
    # TECHNIQUE
    # URL pour l'espace technique (Laboratoire / Radiologie)
    path('technique/examens-a-realiser/', views.liste_examens_techniques, name='liste_examens_techniques'),
    path('technique/saisir-resultats/<int:consultation_id>/', views.saisir_resultats_examens, name='saisir_resultats_examens'),

    # ================================
    # EXAMENS
    path('examens/historique/', views.historique_examens_view, name='historique_examens'),

    # ================================
    # HOSPITALISATION
    path('chambres/', views.dashboard_chambres, name='dashboard_chambres'),
    path('chambres/types/nouveau/', views.ajouter_type_chambre, name='ajouter_type_chambre'),
    path('chambres/nouvelle/', views.ajouter_chambre, name='ajouter_chambre'),
    path('lits/nouveau/', views.ajouter_lit, name='ajouter_lit'),
    path('lits/<int:lit_id>/toggle/', views.toggle_statut_lit, name='lit_toggle_statut'),
    path('hospitalisations/', views.liste_hospitalisations, name='liste_hospitalisations'),
    path('hospitalisations/admettre/', views.admettre_patient, name='admettre_patient'),
    path('hospitalisation/<int:pk>/', views.detail_hospitalisation, name='detail_hospitalisation'),
    path('hospitalisation/<int:pk>/ajouter-suivi/', views.ajouter_suivi, name='ajouter_suivi'),


    # ====================================
    # ORDONNANCE IMPRIMER
    path('ordonnance/imprimer/<int:ordonnance_id>/', views.imprimer_ordonnance, name='imprimer_ordonnance'),


    # ====================================
    # ENTREPRISE
    path('entreprise/enregistrer/', views.enregistrer_entreprise_view, name='enregistrer_entreprise'),
    path('entreprises/', views.liste_entreprises_view, name='liste_entreprises'),

    # =====================================
    # MATERNITE
    path('admettre-maternite/<int:patient_id>/', views.admettre_maternite, name='admettre_maternite'),
    path('maternite/liste/', views.liste_admissions_maternite, name='liste_admissions_maternite'),
    path('maternite/payer/<int:dossier_id>/', views.payer_dossier_maternite, name='payer_dossier_maternite'),
    path('consultation/ajouter/<int:dossier_id>/', views.ajouter_consultation, name='ajouter_consultation'),

    # ====================================
    # DECES
    path('deces/ajouter/', views.enregistrer_deces, name='enregistrer_deces'),
    path('deces/liste/', views.liste_deces, name='liste_deces'),
    path('deces/imprimer/<int:deces_id>/', views.imprimer_deces, name='imprimer_deces'),
    path('deces/payer/<int:deces_id>/', views.enregistrer_paiement_deces, name='enregistrer_paiement_deces'),

    # ====================================
    # SOINS
    path('soin-rapide/', views.enregistrer_soin_rapide, name='soin_rapide'),
    path('soins/liste-traitement/', views.liste_soins_traitement, name='liste_soins_traitement'),
    path('soin/valider/<int:soin_id>/', views.marquer_fait, name='marquer_fait'),
    path('soins/historique/', views.historique_soins, name='historique_soins'),
    path('facture/imprimer/<int:paiement_id>/', views.facture_print, name='facture_print'),


    # =====================================
    # PHARMACIE
    path('pharmacie/ajouter-produit/', views.ajouter_produit, name='ajouter_produit'),
    path('pharmacie/stock/', views.gestion_pharmacie, name='gestion_pharmacie'),
    path('pharmacie/ajouter-lot/', views.ajouter_lot, name='ajouter_lot'),
    path('vente/', views.enregistrer_vente, name='enregistrer_vente'),
    path('vente/dashboard/', views.dashboard_ventes, name='dashboard_ventes'),
    path('ventes/', views.liste_ventes, name='liste_ventes'),
    path('facture/<int:vente_id>/', views.details_facture, name='details_facture'),
    path('vente/valider/', views.valider_vente, name='valider_vente'),


    # =====================================
    # ORIENTATION
    path('service/liste-attente/', views.service_destinataire_view, name='service_liste_attente'),
    path('service/historique/', views.service_historique_view, name='service_historique'),

    # =====================================
    # BLOC OPERATOIRE  
    path('bloc/saisir-compte-rendu/<int:consultation_id>/', views.gerer_bloc_operatoire, name='saisir_compte_rendu_bloc'),
    path('bloc/historique/', views.historique_bloc_operatoire, name='historique_bloc_operatoire'),
    path('caisse/encaisser-bloc/<int:bloc_id>/', views.encaisser_bloc, name='encaisser_bloc'),


 ]
