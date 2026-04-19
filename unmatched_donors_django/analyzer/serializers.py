from rest_framework import serializers
from .models import AnalysisSession, UnmatchedDonor, AnalysisLog


class UnmatchedDonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnmatchedDonor
        fields = [
            'id', 'first_name', 'last_name', 'email', 'address',
            'city', 'state', 'zip_code', 'phone', 'source', 'imported'
        ]
        read_only_fields = ['id', 'imported']


class AnalysisLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisLog
        fields = ['id', 'level', 'message', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class AnalysisSessionSerializer(serializers.ModelSerializer):
    donors_count = serializers.SerializerMethodField()
    processing_time = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisSession
        fields = [
            'id', 'session_id', 'status', 'total_donors',
            'unique_donors', 'unmatched_donors', 'matched_donors',
            'match_rate', 'donors_count', 'processing_time',
            'created_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'session_id', 'total_donors', 'unique_donors',
            'unmatched_donors', 'matched_donors', 'match_rate', 'created_at'
        ]

    def get_donors_count(self, obj):
        return obj.donors.count()

    def get_processing_time(self, obj):
        return obj.processing_time
