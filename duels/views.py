from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

from .models import Duel
from .serializers import DuelSerializer, VoteSerializer
from .permissions import IsAuthenticatedOrReadOnly


class DuelViewSet(viewsets.ModelViewSet):
    queryset = Duel.objects.all()
    serializer_class = DuelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )

    filterset_fields = ('status',)
    search_fields = ('first_cat__name', 'second_cat__name')
    ordering_fields = ('start_time', 'end_time')
    ordering = ('-start_time',)

    def perform_create(self, serializer):
        duel = serializer.save()
        duel.update_status()


    def destroy(self, request, *args, **kwargs):
        duel = self.get_object()
        duel.update_status()

        if duel.status != 'planned':
            return Response(
                {"error": "Можно удалить только запланированную дуэль"},
                status=400
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        duel = self.get_object()

        serializer = VoteSerializer(
            data=request.data,
            context={
                'request': request,
                'duel': duel
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        duel = self.get_object()
        duel.update_status()

        votes = duel.votes.values('cat__name').annotate(count=Count('cat'))

        return Response({
            "duel": duel.id,
            "status": duel.status,
            "results": list(votes)
        })
