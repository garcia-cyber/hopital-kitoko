from django.urls import path
from .views import *
from . import views


urlpatterns = [
    # =================================
    # PAGE D'ACCUEIL front et back 
    #
    path('', home , name = 'home') ,
    path('panel/', panel , name ='panel'),
    # ===================================
    # login et logout
    #
    path('login/' , login , name = 'login'),  
    path('deconnexion/', deconnexion , name='deconnexion') , 
    #=======================================
    # employe add , profil add ,read , update 
    #
    path('employeAdd/', employeAdd , name ='employeAdd') , 
    path('employeRead/',employeRead , name = 'employeRead') , 
    path('profilAdd/<int:user_id>/', profilAdd , name = 'profilAdd'),
    path('profilRead/', profilRead , name = 'profilRead') , 

    # ============================================
    # patient add read 
    #
    path('patientAdd/', patientAdd , name = 'patientAdd') ,
    path('patientRead/' , patientRead , name = 'patientRead') , 
    path('liste_patients_soldes/' , liste_patients_soldes , name ='liste_soldes') ,
    path('patient/<int:patient_id>/archives/', views.dossier_archive_patient, name='dossier_archive_patient'),

    # ===============================================
    # paiement fiche historique
    #
    path('encaisser-fiche/<int:patient_id>/', views.encaisser_fiche, name='encaisser_fiche'),
    path('historique_patient/<int:patient_id>' , historique_patient , name ='historique_patient') ,
    # path('solder-facture/<int:f_id>/', views.solder_facture_view, name='solderFacture'),

    # ================================================
    # infimier
    #
    path('imprimer-recu/<int:paiement_id>/', views.imprimer_recu, name='imprimerRecu'),
    path('imprimer-facture-globale/<int:facture_id>/', views.imprimer_facture_globale, name='imprimerFactureGlobale'),
    path('prendre-signes/<int:patient_id>/', views.prendre_signes, name='prendre_signes'),
    path('historique-signes/', views.historique_signes_vitaux, name='historique_signes'),

    # =================================================
    # medecin 
    #
   
    path('medecin/liste-attente/', views.liste_attente_medecin, name='liste_attente_medecin'),
    path('medecin/consulter/<int:sv_id>/', views.effectuer_consultation, name='effectuer_consultation'),
    path('medecin/patients-consultes/', views.liste_patients_consultes, name='liste_patients_consultes'),

    # ===============================================
    # reception 
    # 
    path('patient/<int:patient_id>/payer_examen/', 
         views.payer_examen, 
         name='payer_examen'),
    
    path('compta/journal/', views.historique_paiements, name='historique_paiements'),
    path('finance/dashboard/', views.tableau_bord_finance, name='tableau_bord_finance'),

    # ===============================================
    # laboratoire
    # 1. La liste des examens payés en attente d'analyse
    path('labo/liste/', views.liste_examens_labo, name='liste_examens_labo'),
    path('labo/saisir-resultat/<int:examen_id>/', views.saisir_resultat_labo, name='saisir_resultat_labo'),



    





]

