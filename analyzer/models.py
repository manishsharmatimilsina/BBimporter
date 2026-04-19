from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class AnalysisSession(models.Model):
    """Store analysis session information"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # File information
    benevity_file = models.FileField(upload_to='uploads/benevity/', null=True, blank=True)
    fup_file = models.FileField(upload_to='uploads/fup/', null=True, blank=True)
    paypal_file = models.FileField(upload_to='uploads/paypal/', null=True, blank=True)
    stripe_file = models.FileField(upload_to='uploads/stripe/', null=True, blank=True)
    globalgiving_file = models.FileField(upload_to='uploads/globalgiving/', null=True, blank=True)
    bb_file = models.FileField(upload_to='uploads/bb/', null=True, blank=True)

    # Results
    total_donors = models.IntegerField(default=0)
    unique_donors = models.IntegerField(default=0)
    unmatched_donors = models.IntegerField(default=0)
    matched_donors = models.IntegerField(default=0)
    match_rate = models.FloatField(default=0.0)

    # Summary JSON
    summary = models.JSONField(default=dict, blank=True)
    source_breakdown = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Analysis {self.session_id} - {self.get_status_display()}"

    @property
    def processing_time(self):
        """Calculate processing time"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_complete(self):
        return self.status == 'completed'

    @property
    def all_files_uploaded(self):
        required_files = [
            self.benevity_file,
            self.fup_file,
            self.paypal_file,
            self.stripe_file,
            self.bb_file
        ]
        return all(required_files)


class UnmatchedDonor(models.Model):
    """Store unmatched donor records"""
    SOURCE_CHOICES = [
        ('benevity', 'BENEVITY'),
        ('fup', 'FUP RAW'),
        ('paypal', 'PAYPAL'),
        ('stripe', 'STRIPE'),
        ('globalgiving', 'GLOBALGIVING'),
    ]

    analysis = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='donors')

    # Donor information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=False)

    # Address
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)

    # Source
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    # BB import info
    import_id = models.CharField(max_length=20, blank=True)
    imported = models.BooleanField(default=False)
    imported_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['source', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['analysis', 'source']),
            models.Index(fields=['email']),
            models.Index(fields=['imported']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class AnalysisLog(models.Model):
    """Log analysis activities"""
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]

    analysis = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.get_level_display()}] {self.message[:50]}"
