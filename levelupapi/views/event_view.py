"""View module for handling requests about games"""
from django.core.exceptions import ValidationError
from rest_framework import fields, status
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from levelupapi.models import Game, Gamer, Event
from django.contrib.auth.models import User

class EventView(ViewSet):
    def create(self, request):
        organizer = Gamer.objects.get(user=request.auth.user)
        game = Game.objects.get(pk=request.data['gameId'])

        try:
            event = Event.objects.create(
                game=game,
                organizer=organizer,
                description=request.data['description'],
                date=request.data['date'],
                time=request.data['time']
            )
            event_serializer = EventSerializer(event, context={'request': request})
            return Response(event_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        events = Event.objects.all()
        event_serializer = EventSerializer(events, many=True)
        return Response(event_serializer.data)

    def retrieve(self, request, pk):
        event = Event.objects.get(pk=pk)
        event_serializer = EventSerializer(event, context={'request': request})
        return Response(event_serializer.data)

    def destroy(self, request, pk):
        event = Event.objects.get(pk=pk)
        event.delete()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, pk):
        event = Event.objects.get(pk=pk)
        event.description =request.data['description']
        event.date = request.data['date']
        event.time = request.data['time']
        event.game = Game.objects.get(pk=request.data['gameId'])
        event.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True)
    def signup(self, request, pk=None):

        # Django uses the `Authorization` header to determine
        # which user is making the request to sign up
        gamer = Gamer.objects.get(user=request.auth.user)

        try:
            # Handle the case if the client specifies a game
            # that doesn't exist
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {'message': 'Event does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # A gamer wants to sign up for an event
        if request.method == "POST":
            try:
                # Using the attendees field on the event makes it simple to add a gamer to the event
                # .add(gamer) will insert into the join table a new row the gamer_id and the event_id
                event.attendees.add(gamer)
                return Response({}, status=status.HTTP_201_CREATED)
            except Exception as ex:
                return Response({'message': ex.args[0]})

        # User wants to leave a previously joined event
        elif request.method == "DELETE":
            try:
                # The many to many relationship has a .remove method that removes the gamer from the attendees list
                # The method deletes the row in the join table that has the gamer_id and event_id
                event.attendees.remove(gamer)
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            except Exception as ex:
                return Response({'message': ex.args[0]})


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class GamerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Gamer
        fields = ['user']

class EventSerializer(serializers.ModelSerializer):
    organizer = GamerSerializer()

    class Meta:
        model = Event
        fields = ['id', 'organizer', 'game', 'date', 'time', 'description']