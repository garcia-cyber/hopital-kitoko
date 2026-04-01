from django.urls import path
from .views import *


urlpatterns = [
    # PAGE D'ACCUEIL front et back 
    #
    path('', home , name = 'home') ,
    path('panel/', panel , name ='panel'),

    # login et logout
    #
    path('login/' , login , name = 'login'),  
    path('deconnexion/', deconnexion , name='deconnexion') , 

    # employe add , profil ,read , update 
    #
    path('employeAdd/', employeAdd , name ='employeAdd') , 

]

