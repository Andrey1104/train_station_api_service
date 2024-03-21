import math

from django.core.exceptions import ValidationError
from django.db import models

from train_station_service.train_station_service import settings


class TrainType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Train(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cargo_num = models.IntegerField()
    places_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(TrainType, on_delete=models.CASCADE, related_name="trains")

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        ordering = ["name"]
        unique_together = ["cargo_num", "places_in_cargo"]
        verbose_name_plural = "trains"


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        ordering = ["name"]


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes"
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes"
    )

    @property
    def distance(self) -> float:
        radius_of_planet = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [
            self.source.latitude,
            self.source.longitude,
            self.destination.latitude,
            self.destination.longitude
        ])
        different_long = lon2 - lon1
        different_lat = lat2 - lat1

        temp = (
            math.sin(different_lat / 2)
            ** 2 + math.cos(lat1) * math.cos(lat2)
            * math.sin(different_long / 2) ** 2
        )

        distance = 2 * math.atan2(math.sqrt(temp), math.sqrt(1 - temp))

        return round(radius_of_planet * distance)

    def __str__(self) -> str:
        return f"{self.distance} km"


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name"]


class Trip(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="trips")
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="trips")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    def __str__(self) -> str:
        return f"train: {self.train}, distance: {self.route}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")

    @staticmethod
    def validate_ticket(cargo_num, places_in_cargo, trip, error_to_raise):
        for ticket_attr_value, ticket_attr_name, train_attr_name in [
            (cargo_num, "cargo", "cargo_num"),
            (places_in_cargo, "seat", "places_in_cargo"),
        ]:
            count_attrs = getattr(trip, train_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {train_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.cargo,
            self.seat,
            self.trip.train,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return (
            f"{str(self.trip)} (cargo: {self.cargo}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("trip", "cargo", "seat")
        ordering = ["cargo", "seat"]
