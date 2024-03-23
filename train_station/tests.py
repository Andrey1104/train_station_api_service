import tempfile
import os
from datetime import datetime

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import Train, TrainType, Route, Station, Trip
from train_station.serializer import TrainSerializer, TripDetailSerializer


TRAIN_URL = reverse("train_station:train-list")
TRIP_URL = reverse("train_station:trip-list")


def sample_train_type():
    train_type, _ = TrainType.objects.get_or_create(name="test")
    return train_type


def sample_train(**params):

    defaults = {
        "name": "Sample train",
        "cargo_num": 10,
        "places_in_cargo": 50,
        "train_type": sample_train_type(),
    }
    defaults.update(params)
    train, _ = Train.objects.get_or_create(**defaults)
    return train


def sample_trip(**params):
    train = sample_train()
    station1 = Station.objects.create(
        name="Station1",
        latitude=50.50,
        longitude=48.49
    )
    station2 = Station.objects.create(
        name="Station2",
        latitude=51.50,
        longitude=46.49
    )
    route = Route.objects.create(
        source=station1,
        destination=station2
    )

    defaults = {
        "route": route,
        "train": train,
        "departure_time": datetime.now(),
        "arrival_time": datetime.now(),
    }
    defaults.update(params)

    return Trip.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for recipe image upload"""
    return reverse("train_station:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("train_station:trip-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_trains(self):
        sample_train()
        res = self.client.get(TRAIN_URL)
        trains = Train.objects.order_by("id")
        serializer = TrainSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_trip_detail(self):
        trip = sample_trip()
        url = detail_url(trip.id)
        res = self.client.get(url)
        serializer = TripDetailSerializer(trip)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        train_type = TrainType.objects.create(name="train_type")
        payload = {
            "name": "Blue",
            "cargo_num": 20,
            "places_in_cargo": 20,
            "train_type": train_type
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.train = sample_train()
        self.trip = sample_trip(train=self.train)
        self.image_url = image_upload_url(self.train.id)

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(self.image_url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_url_is_shown_on_train_list(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(self.image_url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_URL)

        self.assertIn("image", res.data[0].keys())

    def test_image_url_in_train_detail(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_URL)

        self.assertIn("image", res.data[0].keys())

    def test_put_train_not_allowed(self):
        payload = {
            "name": "test1",
        }
        train_type = sample_train_type()
        url = detail_url(train_type.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST | status.HTTP_404_NOT_FOUND)

    def test_delete_train_not_allowed(self):
        train_type = TrainType.objects.create(name="test10")
        url = detail_url(train_type.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
