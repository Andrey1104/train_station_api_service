from datetime import datetime

from django.db.models import F, Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from rest_framework.viewsets import GenericViewSet

from train_station.models import (
    Crew,
    TrainType,
    Train,
    Trip,
    Station,
    Route,
    Order,
)
from train_station.permissions import IsAdminOrIfAuthenticatedReadOnly

from train_station.serializer import (
    TrainSerializer,
    TripSerializer,
    TrainTypeSerializer,
    CrewSerializer,
    OrderSerializer,
    StationSerializer,
    TripListSerializer,
    TripDetailSerializer,
    OrderListSerializer,
    RouteSerializer,
    RouteListSerializer, TrainImageSerializer
)


class TrainTypeViewSet(
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class TrainViewSet(
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Train.objects.all().select_related("train_type")
    serializer_class = TrainSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific train"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TripViewSet(viewsets.ModelViewSet):
    queryset = (
        Trip.objects.all()
        .select_related("route", "train")
        .annotate(
            tickets_available=(
                F("train__cargo_num") * F("train__places_in_cargo")
                - Count("tickets")
            )
        )
    )
    serializer_class = TripSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        date = self.request.query_params.get("date")
        route_id_str = self.request.query_params.get("route")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=date)

        if route_id_str:
            queryset = queryset.filter(route_id=int(route_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TripListSerializer

        if self.action == "retrieve":
            return TripDetailSerializer

        return TripSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "route",
                type=OpenApiTypes.INT,
                description="Filter by route id (ex. ?route=2)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description=(
                    "Filter by datetime of departure"
                    "(ex. ?date=2022-10-23)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RouteViewSet(
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAdminOrIfAuthenticatedReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        return RouteSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 50


class OrderViewSet(
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Order.objects.prefetch_related(
        "tickets__trip__train", "tickets__train__route"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StationViewSet(
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class CrewViewSet(
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
