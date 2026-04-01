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

    # profil 
    # 
    profil = Profil.objects.filter(userProfil = request.user).first()
    fonction = profil.fonction.fonction if profil else None 

    context = {
    'nbrU' : use ,
    'fonction': fonction ,
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


    