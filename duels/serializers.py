from rest_framework import serializers
from .models import Duel, Vote


class DuelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Duel
        fields = '__all__'

        read_only_fields = ['start_time', 'end_time', 'status']

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        if instance:
            instance.update_status()

            if instance.status in ['active', 'finished']:
                raise serializers.ValidationError(
                    "Нельзя изменять дуэль после её начала"
                )

        first_cat = data.get('first_cat', getattr(self.instance, 'first_cat', None))
        second_cat = data.get('second_cat', getattr(self.instance, 'second_cat', None))

        if first_cat == second_cat:
            raise serializers.ValidationError("Коты должны быть разными")
        return data


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'cat']
        read_only_fields = ['id']

    def validate(self, data):
        request = self.context['request']
        duel = self.context['duel']
        cat = data['cat']

        duel.update_status()

        if duel.status != 'active':
            raise serializers.ValidationError("Дуэль не активна")

        if cat not in [duel.first_cat, duel.second_cat]:
            raise serializers.ValidationError("Этот кот не участвует в дуэли")

        if getattr(cat, "owner", None) == request.user:
            raise serializers.ValidationError("Нельзя голосовать за своего кота")

        if Vote.objects.filter(user=request.user, duel=duel).exists():
            raise serializers.ValidationError("Вы уже голосовали")

        return data

    def create(self, validated_data):
        duel = self.context.get('duel')

        return Vote.objects.create(
            user=self.context['request'].user,
            cat=validated_data['cat'],
            duel=duel
        )
