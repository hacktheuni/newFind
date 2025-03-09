from django.urls import path
from . import views

urlpatterns = [
    path('', views.listDSC, name='listDSC'),
    path('listDSC', views.listDSC, name='listDSC'),
    path('listWork', views.listWork, name='listWork'),
    path('listPendingWork', views.listPendingWork, name='listPendingWork'),
    path('listAnnual', views.listAnnual, name='listAnnual'),
    path('listCompany', views.listCompany, name='listCompany'),
    path('listGroup', views.listGroup, name='listGroup'),
    path('listClient', views.listClient, name='listClient'),
    path('listReport', views.listReport, name='listReport'),
    path('addDSC', views.addDSC, name='addDSC'),
    path('addWork', views.addWork, name='addWork'),
    path('addPendingWork', views.addPendingWork, name='addPendingWork'),
    path('addAnnual', views.addAnnual, name='addAnnual'),
    path('addCompany', views.addCompany, name='addCompany'),
    path('addGroup', views.addGroup, name='addGroup'),
    path('addClient', views.addClient, name='addClient'),
    path('updateDSC/<int:dscID>/', views.updateDSC, name='updateDSC'),
    path('updateWork/<int:formID>/', views.updateWork, name='updateWork'),
    path('updatePendingWork/<int:pendingWorkID>/', views.updatePendingWork, name='updatePendingWork'),
    path('updateAnnual/<int:annualFilingID>/', views.updateAnnual, name='updateAnnual'),
    path('updateCompany/<int:companyID>/', views.updateCompany, name='updateCompany'),
    path('updateGroup/<int:groupID>/', views.updateGroup, name='updateGroup'),
    path('updateClient/<int:clientID>/', views.updateClient, name='updateClient'),
    path('deleteDSC', views.deleteDSC, name='deleteDSC'),
    path('deleteWork', views.deleteWork, name='deleteWork'),
    path('deletePendingWork', views.deletePendingWork, name='deletePendingWork'),
    path('deleteAnnual', views.deleteAnnual, name='deleteAnnual'),
    path('deleteCompany', views.deleteCompany, name='deleteCompany'),
    path('deleteGroup', views.deleteGroup, name='deleteGroup'),
    path('deleteClient', views.deleteClient, name='deleteClient'),
    path('feedBack', views.feedBack, name='feedBack'),
    path('fetchGroupName', views.fetchGroupName, name='fetchGroupName'),
    path('fetchFormDetails', views.fetchFormDetails, name='fetchFormDetails'),
    path('updatePassword', views.updatePassword, name='updatePassword'),



]