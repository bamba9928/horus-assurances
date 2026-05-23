from rest_framework import serializers


class DashboardCountsSerializer(serializers.Serializer):
    groups = serializers.IntegerField()
    users = serializers.IntegerField()
    contributors = serializers.IntegerField()
    clients = serializers.IntegerField()
    vehicles = serializers.IntegerField()
    quotes = serializers.IntegerField()
    payments = serializers.IntegerField()
    confirmed_payments = serializers.IntegerField()
    contracts = serializers.IntegerField()
    issued_contracts = serializers.IntegerField()
    commissions = serializers.IntegerField()
    wallets = serializers.IntegerField()
    audit_logs = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    scope = serializers.CharField()
    counts = DashboardCountsSerializer()
