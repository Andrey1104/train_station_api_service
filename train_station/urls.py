from django.urls import path, include
from rest_framework import routers

from train_station.views import (
    TrainViewSet,
    TripViewSet,
    TrainTypeViewSet,
    CrewViewSet,
    OrderViewSet,
    RouteViewSet,
    StationViewSet
)


router = routers.DefaultRouter()

router.register("trains", TrainViewSet)
router.register("train_types", TrainTypeViewSet)
router.register("trips", TripViewSet)
router.register("crews", CrewViewSet)
router.register("orders", OrderViewSet)
router.register("routes", RouteViewSet)
router.register("stations", StationViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "train_station"
