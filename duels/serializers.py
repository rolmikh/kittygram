from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from .models import Duel, Vote, CatStats, Tournament


class DuelSerializer(serializers.ModelSerializer):

    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Duel
        fields = '__all__'
        read_only_fields = [
            'status',
            'winner',
            'is_draw',
            'created_at',
            'start_time',
            'end_time'
        ]


    def validate(self, data):

        first_cat = data.get(
            'first_cat',
            self.instance.first_cat if self.instance else None
        )

        second_cat = data.get(
            'second_cat',
            self.instance.second_cat if self.instance else None
        )

        if first_cat == second_cat:
            raise serializers.ValidationError(
                'Коты должны быть разными'
            )

        return data


class VoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vote
        fields = ['cat']

    def validate(self, data):
        request = self.context['request']
        duel = self.context['duel']
        cat = data['cat']

        duel.refresh_status()

        if duel.status != Duel.STATUS_ACTIVE:
            raise serializers.ValidationError("Дуэль не активна")

        if cat not in [duel.first_cat, duel.second_cat]:
            raise serializers.ValidationError("Кот не участвует в дуэли")

        if Vote.objects.filter(user=request.user, duel=duel).exists():
            raise serializers.ValidationError("Вы уже голосовали")

        if cat.owner == request.user:
            raise serializers.ValidationError("Нельзя голосовать за своего кота")

        return data

    def create(self, validated_data):
        return Vote.objects.create(
            user=self.context['request'].user,
            duel=self.context['duel'],
            cat=validated_data['cat']
        )


class CatStatsSerializer(serializers.ModelSerializer):
    cat_name = serializers.CharField(source='cat.name', read_only=True)
    cat_id = serializers.IntegerField(source='cat.id', read_only=True)

    class Meta:
        model = CatStats
        fields = ['id', 'cat_id', 'cat_name', 'wins', 'losses', 'draws', 'total_duels', 'rating']


class TournamentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tournament
        fields = '__all__'
        read_only_fields = [
            'winner',
            'status',
            'created_at',
        ]

    def validate(self, data):
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date is not None and end_date is not None:
            if end_date <= start_date:
                raise serializers.ValidationError("Дата окончания должна быть позже начала")

        return data
