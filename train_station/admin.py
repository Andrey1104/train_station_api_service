from django.contrib import admin

from train_station.models import (
    Train,
    TrainType,
    Trip,
    Ticket,
    Station,
    Route,
    Crew,
    Order
)

admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Trip)
admin.site.register(Ticket)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Crew)
admin.site.register(Order)
