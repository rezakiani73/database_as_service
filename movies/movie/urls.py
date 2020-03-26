from django.conf.urls import url
from . import views

app_name = 'movie'
urlpatterns = [
    url(r'^$', views.login, name='login'),
    url(r'^main/$',views.index, name='index'),
    url(r'^register_handler/$', views.register_handler, name='register_handler'),
    url(r'^user_Authenticate/$', views.user_Authenticate, name='user_Authenticate'),
    url(r'^create_database/$', views.create_database, name='create_database'),
    url(r'^adminPage/$', views.adminPage, name='adminPage'),
    url(r'^myprofile/index.html/$', views.profile, name='profile'),
    url(r'^myprofile/form.html/$', views.profiel_form, name='profiel_form'),
    url(r'^country/$', views.country, name='country'),
    url(r'^add_country/$', views.add_country, name='add_country'),
    url(r'^update_country/$', views.update_country, name='update_country'),
    url(r'^delete_country/$', views.delete_country, name='delete_country'),
    url(r'^director/$', views.director, name='director'),
    url(r'^add_director/$', views.add_director, name='add_director'),
    url(r'^delete_director/$', views.delete_director, name='delete_director'),
    url(r'^movie/$', views.movie, name='movie'),
    url(r'^add_movie/$', views.add_movie, name='add_movie'),
    url(r'^delete_movie/$', views.delete_movie, name='delete_movie'),
    url(r'^create_db_info/$', views.create_db_info, name='create_db_info'),
    url(r'^request/$', views.send_request, name='request'),
    url(r'^verify/$', views.verify , name='verify'),
    url(r'^show_info/(?P<user_name>.*)/$', views.show_info , name='show_info'),
]
