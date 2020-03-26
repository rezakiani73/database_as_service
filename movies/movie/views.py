from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from . import connection
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponse
from django.shortcuts import redirect
from zeep import Client
import jdatetime



try:
    client = connection.Connection('root', 'root', '0.0.0.0', 6543)
except:
    pass


# Create your views here..
# process on sign up page and return alert and rediret
def register_handler(request):
    global client
    fname=request.POST.get('firstname', False)
    lname=request.POST.get('lastname', False)
    email=request.POST.get('email', False)
    username = request.POST.get('username', False)
    password = request.POST.get('pass', False)
    password_repeat = request.POST.get('pass-repeat', False)
    if password == password_repeat:
        if username and password:
            client.create_user(username, password)
            User.objects.create_user(first_name=fname,last_name=lname,email=email,username=username, password=password,)
            messages.success(request, 'Your registration has been successfully completed')
        else:
            messages.error(request, 'Registration was encountered error')
    else:
        messages.warning(request, 'your password is not equal')

    return HttpResponseRedirect(reverse('movie:login'))


# render login page
def login(request):
    return render(request, 'movie/login.html', {})


# process on login page and redirect
def user_Authenticate(request):
    username = request.POST.get('uname', False)
    password = request.POST.get('psw', False)
    if username and password =='admin':
        return HttpResponseRedirect(reverse('movie:adminPage'))
    else:
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return HttpResponseRedirect(reverse('movie:profile'))

        else:
            messages.error(request, 'Your account is not logged in. Please register')
            return HttpResponseRedirect(reverse('movie:login'))


# render index.html file
def profile(request):
    global client
    now_date=jdatetime.date.today().strftime("%d /%m /%Y")
    top_name = request.user.username
    db_user = client.return_user_dbs(top_name)
    chart_items = client.chart_doughnut(top_name)
    if db_user == 'false':
        no_dbs = 'There are no databases'
    else:
        no_dbs = 'not null'
    Percentage = []
    if chart_items[0][0]!=None:
        if chart_items[0][4]==0:
            chart_items[0][4]=1

        for i in range(0, len(chart_items[0])-1):
            Percentage.append(round((chart_items[0][i] * 100) / chart_items[0][4], 2))
    total_cost=0
    if db_user=='false':
        total_cost=0
    else:
        for i in db_user:
            total_cost+=i[6]
    return render(request, 'gentelella/index.html',
                  {'top_name': top_name, 'db_user': db_user, 'no_dbs': no_dbs, 'chart_items': chart_items[0],
                   'Percentage': Percentage,'now_date':now_date,'total_cost':total_cost})


# render form.html file
def profiel_form(request):
    global client
    now_date=jdatetime.date.today().strftime("%d /%m /%Y")
    top_name = request.user.username
    database_name = request.POST.get('db_name', False)
    if database_name:
        db = top_name + "_" + database_name
        client.insert_db_info(top_name, db)
        client.create_database(db)
        return HttpResponseRedirect(reverse('movie:profiel_form'))

    db_user = client.return_user_dbs(top_name)
    return render(request, 'gentelella/form.html', {'top_name': top_name, 'db_user': db_user,'now_date':now_date})


def create_db_info(request):
    global client
    client.create_db_info()
    return HttpResponse('Done')


def send_request(request):
    global client
    db_user = client.return_user_dbs(request.user.username)
    total_cost=0
    if db_user=='false':
        total_cost=0
    else:
        for i in db_user:
            total_cost+=i[6]
    MERCHANT = '00000000-0000-0000-0000-000000000000'
    client1 = Client('https://sandbox.zarinpal.com/pg/services/WebGate/wsdl')
    amount = total_cost  # Toman / Required
    description = "تراکنش استفاده از سیستم دیتابیس به عنوان خدمت ابری"# Required
    email = 'DBAS@db.ir'  # Optional
    mobile = '09123456789'  # Optional
    CallbackURL = 'http://93.118.97.199:8085/verify/' # Important: need to edit for realy server.
    result = client1.service.PaymentRequest(MERCHANT, amount, description, email, mobile, CallbackURL)
    if result.Status == 100:
        return redirect('https://sandbox.zarinpal.com/pg/StartPay/' + str(result.Authority))
    else:
        return HttpResponse('Error code: ' + str(result.Status))



def verify(request):
    global client
    myUser=request.user.username
    db_user = client.return_user_dbs(myUser)
    total_cost=0
    if db_user=='false':
        total_cost=0
    else:
        for i in db_user:
            total_cost+=i[6]
    MERCHANT = '00000000-0000-0000-0000-000000000000'
    client1 = Client('https://sandbox.zarinpal.com/pg/services/WebGate/wsdl')
    amount = total_cost  # Toman / Required
    if request.GET.get('Status') == 'OK':
        result = client1.service.PaymentVerification(MERCHANT, request.GET['Authority'], amount)
        if result.Status == 100:
            client.payment_action(myUser)
            # return HttpResponse('Transaction success.\nRefID: ' + str(result.RefID))

            return HttpResponseRedirect(reverse('movie:profile'))
        elif result.Status == 101:
            return HttpResponse('Transaction submitted : ' + str(result.Status))
        else:
            return HttpResponse('Transaction failed.\nStatus: ' + str(result.Status))
    else:
        return HttpResponse('Transaction failed or canceled by user')



def adminPage(request):
    now_date=jdatetime.date.today().strftime("%d /%m /%Y")
    users=User.objects.all()
    # usernames = User.objects.values_list('email', flat=True)
    for i in users:
        print (i.email)
    return render(request,'gentelella/tables.html',{'now_date':now_date,'users':users})

def show_info(request,user_name):
    global client
    now_date=jdatetime.date.today().strftime("%d /%m /%Y")
    db_user = client.return_user_dbs(user_name)
    chart_items = client.chart_doughnut(user_name)
    if db_user == 'false':
        no_dbs = 'There are no databases'
    else:
        no_dbs = 'not null'
    Percentage = []
    if chart_items[0][0]!=None:
        if chart_items[0][4]==0:
            chart_items[0][4]=1

        for i in range(0, len(chart_items[0])-1):
            Percentage.append(round((chart_items[0][i] * 100) / chart_items[0][4], 2))
    total_cost=0
    if db_user=='false':
        total_cost=0
    else:
        for i in db_user:
            total_cost+=i[6]
    return render(request, 'gentelella/index.html',
                  {'top_name': user_name, 'db_user': db_user, 'no_dbs': no_dbs, 'chart_items': chart_items[0],
                   'Percentage': Percentage,'now_date':now_date,'total_cost':total_cost})






def create_database(request):
    global client
    # client.create_database('nano')
    client.use_database('sajjad_userInfo')
    client.create_table('j', {'id': 'int', 'name': 'text'}, ['id'])
    # client.create_table('jamali', {'id': 'int', 'first_name': 'text', 'last_name': 'text', 'date_of_birth': 'text'},
    #                     ['id'])
    # client.create_table('jamshidi',
    #                     {'id': 'int', 'name': 'text', 'director_id': 'int', 'country_id': 'int', 'year': 'text',
    #                      'description': 'text'}, ['id'])
    return HttpResponse('Done')

def index(request):
    global client
    client.use_database('movie')
    movie_table = client.table('movie')
    movies = movie_table.get_item()

    country_table = client.table('country')
    countries = country_table.get_item()

    director_table = client.table('director')
    directors = director_table.get_item()

    for i in range(0, len(movies)):
        for country in countries:
            if int(country['id']) == int(movies[i]['country_id']):
                movies[i]['country_name'] = country['name']
        for director in directors:
            if int(director['id']) == int(movies[i]['director_id']):
                movies[i]['director_name'] = director['first_name'] + " " + director['last_name']
    return render(request, 'movie/index.html', {'movies': movies})


def country(request):
    global client
    client.use_database('jamshidi_reza_salam')
    table = client.table('ahmadi')
    rows = table.get_item()
    return render(request, 'movie/country.html', {'rows': rows})


def add_country(request):
    global client
    client.use_database('jamshidi_reza_salam')
    # client.use_database('movie')
    table = client.table('ahmadi')
    id = request.POST['id']
    name = request.POST['name']
    table.put_item({'id': int(id), 'name': name})
    return HttpResponseRedirect(reverse('movie:country'))


def update_country(request):
    global client
    client.use_database('jamshidi_reza_salam')
    table = client.table('ahmadi')
    id = request.POST['id']
    name = request.POST['name']
    table.update_item({'name': name}, {'id': int(id)})
    return HttpResponseRedirect(reverse('movie:country'))


def delete_country(request):
    global client
    client.use_database('jamshidi_reza_salam')
    table = client.table('ahmadi')
    id = request.GET['id']
    table.delete_item({'id': int(id)})
    return HttpResponseRedirect(reverse('movie:country'))


def director(request):
    global client
    client.use_database('movie')
    table = client.table('director')
    rows = table.get_item()
    return render(request, 'movie/director.html', {'rows': rows})


def add_director(request):
    global client
    client.use_database('movie')
    table = client.table('director')
    id = request.POST['id']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    date_of_birth = request.POST['date_of_birth']
    table.put_item({'id': int(id), 'first_name': first_name, 'last_name': last_name, 'date_of_birth': date_of_birth})
    return HttpResponseRedirect(reverse('movie:director'))


def delete_director(request):
    global client
    client.use_database('movie')
    table = client.table('director')
    id = request.GET['id']
    table.delete_item({'id': int(id)})
    return HttpResponseRedirect(reverse('movie:director'))


def movie(request):
    global client
    client.use_database('movie')
    table1 = client.table('movie')
    rows = table1.get_item()

    table2 = client.table('director')
    directors = table2.get_item()

    table3 = client.table('country')
    countries = table3.get_item()
    return render(request, 'movie/movie.html', {'rows': rows, 'directors': directors, 'countries': countries})


def add_movie(request):
    global client
    client.use_database('movie')
    table = client.table('movie')
    id = int(request.POST['id'])
    name = request.POST['name']
    director_id = int(request.POST['director_id'])
    country_id = int(request.POST['country_id'])
    year = request.POST['year']
    description = request.POST['description']
    table.put_item({'id': id, 'name': name, 'director_id': director_id, 'country_id': country_id, 'year': year,
                    'description': description})
    return HttpResponseRedirect(reverse('movie:movie'))


def delete_movie(request):
    global client
    client.use_database('movie')
    table = client.table('movie')
    id = request.GET['id']
    table.delete_item({'id': int(id)})
    return HttpResponseRedirect(reverse('movie:movie'))


