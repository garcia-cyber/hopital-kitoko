from django.urls import path
from .views import *


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


]

