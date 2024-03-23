from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from train_station.models import (
    Crew,
    TrainType,
    Train,
    Trip,
    Ticket,
    Station,
    Route,
    Order,
)


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    train_type = serializers.CharField(source="train_type.name")

    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "places_in_cargo", "train_type", "image")


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    source = StationSerializer
    destination = StationSerializer

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(read_only=True)
    destination = serializers.CharField(read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["seat"],
            attrs["trip"].train,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "trip")


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("cargo", "seat")


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ("id", "route", "train", "crew", "departure_time", "arrival_time")


class TripListSerializer(TripSerializer):
    train = serializers.CharField(source="train.name", read_only=True)
    distance = serializers.ReadOnlyField(
        source="route.distance", read_only=True
    )
    route = serializers.CharField(source="route.name", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Trip
        fields = (
            "id",
            "train",
            "route",
            "distance",
            "tickets_available",
        )


class TripDetailSerializer(TripSerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = Trip
        fields = ("id", "train", "route", "crew", "taken_places")


class TicketListSerializer(TicketSerializer):
    trip = TripDetailSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
