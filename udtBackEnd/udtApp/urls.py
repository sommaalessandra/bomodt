from django.urls import path

from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("", views.index, name="index"),
    path("index", views.index, name="index"),
    path("monitor", views.monitor, name="monitor"),
    path("entityList", views.entityList, name='entityList'),
    path("entityList/<str:entity_id>", views.entity, name='entity'),
    path("simulationModeler", views.simulationModeler, name='simulationModeler'),
    path("simulation", views.simulation, name='simulation'),
    path("simulation/<str:folder>/", views.serve_image, name='serve_image'),
    path("simulationResults", views.simulationResults, name='simulationResults'),
    path("simulationResults/<str:folder_name>/", views.serveResults, name='serveResults'),
    path("image/<str:folder_name>/", views.serve_image, name="serve_image"),
    path('summary', views.mocksummary, name='summary'),
]
