from django.shortcuts import render , redirect , get_object_or_404
from .forms import * 
from django.contrib.auth import authenticate , login as auth , logout 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User
from .models import *

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
