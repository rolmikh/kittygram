from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta
from django.utils import timezone

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from .models import (
    Duel,
    CatStats,
    Vote,
    Tournament
)

from .serializers import (
    DuelSerializer,
    VoteSerializer,
    CatStatsSerializer,
    TournamentSerializer
)


class DuelViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post']

    queryset = Duel.objects.all()

    serializer_class = DuelSerializer

    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )

    filterset_fields = ('status',)

    search_fields = (
        'first_cat__name',
        'second_cat__name'
    )

    ordering_fields = (
        'created_at',
        'start_time'
    )

    ordering = ('-created_at',)

    def get_queryset(self):

        queryset = Duel.objects.all()

        for duel in queryset:
            duel.refresh_status()

        return queryset

    def retrieve(self, request, *args, **kwargs):

        duel = self.get_object()

        duel.refresh_status()

        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):

        duel = serializer.save()

        duel.refresh_status()

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
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

        return Response(
            {'detail': 'vote accepted'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):

        duel = self.get_object()

        duel.refresh_status()

        first_votes = duel.votes.filter(
            cat=duel.first_cat
        ).count()

        second_votes = duel.votes.filter(
            cat=duel.second_cat
        ).count()

        return Response({
            'duel_id': duel.id,
            'status': duel.status,
            'first_cat_votes': first_votes,
            'second_cat_votes': second_votes,
            'winner': (
                duel.winner.name
                if duel.winner else None
            ),
            'is_draw': duel.is_draw
        })

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):

        stats = CatStats.objects.select_related(
            'cat'
        ).order_by('-rating')

        serializer = CatStatsSerializer(
            stats,
            many=True
        )

        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def my_vote_stats(self, request):

        user_votes = Vote.objects.filter(
            user=request.user
        ).select_related('duel')

        total_votes = user_votes.count()

        successful_votes = 0

        failed_votes = 0

        pending_votes = 0

        for vote in user_votes:

            duel = vote.duel

            duel.refresh_status()

            if duel.status != Duel.STATUS_FINISHED:

                pending_votes += 1

            elif duel.winner_id == vote.cat_id:

                successful_votes += 1

            else:

                failed_votes += 1

        return Response({
            'total_votes': total_votes,
            'successful_votes': successful_votes,
            'failed_votes': failed_votes,
            'pending_votes': pending_votes
        })
    
    @action(
    detail=True,
    methods=['post'],
    permission_classes=[IsAuthenticated]
    )
    def start(self, request, pk=None):

        duel = self.get_object()

        if duel.status != Duel.STATUS_PLANNED:
            return Response(
                {'detail': 'Дуэль уже началась'},
                status=status.HTTP_400_BAD_REQUEST
            )

        duel.start_time = timezone.now()

        duel.end_time = (
            duel.start_time + timedelta(hours=1)
        )

        duel.status = Duel.STATUS_ACTIVE

        duel.save(update_fields=[
            'start_time',
            'end_time',
            'status'
        ])

        return Response({
            'detail': 'Дуэль началась'
        })


class TournamentViewSet(viewsets.ModelViewSet):

    http_method_names = ['get', 'post']

    queryset = Tournament.objects.all()

    serializer_class = TournamentSerializer

    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter
    )

    filterset_fields = ('status',)

    ordering_fields = (
        'created_at',
        'start_date'
    )

    ordering = ('-created_at',)

    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):

        tournament = self.get_object()

        finished_duels = tournament.duels.filter(
            status=Duel.STATUS_FINISHED
        )

        stats = {}

        for duel in finished_duels:

            if duel.winner:

                winner_name = duel.winner.name

                stats[winner_name] = (
                    stats.get(winner_name, 0) + 1
                )

        sorted_stats = sorted(
            stats.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return Response(sorted_stats)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):

        tournament = self.get_object()

        tournament.update_results()

        return Response({
            'tournament': tournament.name,
            'status': tournament.status,
            'winner': (
                tournament.winner.name
                if tournament.winner else None
            )
        })
