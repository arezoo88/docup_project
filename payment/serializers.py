from rest_framework import serializers

from payment.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model=Transaction
        fields="__all__"



class BriefTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model=Transaction
        fields="__all__"
