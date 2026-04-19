from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import uuid
import json

from .models import AnalysisSession, UnmatchedDonor, AnalysisLog
from .forms import AnalysisForm
from .serializers import AnalysisSessionSerializer, UnmatchedDonorSerializer
from .tasks import process_analysis
from .utils import analyze_donors


class AnalysisSessionViewSet(viewsets.ModelViewSet):
    """API ViewSet for Analysis Sessions"""
    queryset = AnalysisSession.objects.all()
    serializer_class = AnalysisSessionSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return AnalysisSession.objects.filter(user=self.request.user)
        return AnalysisSession.objects.none()

    def create(self, request, *args, **kwargs):
        """Create new analysis session"""
        session_id = str(uuid.uuid4())[:12]
        analysis = AnalysisSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id
        )
        serializer = self.get_serializer(analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def upload_file(self, request, pk=None):
        """Upload a file to analysis session"""
        analysis = self.get_object()
        file_type = request.data.get('file_type')
        file_obj = request.FILES.get('file')

        if not file_type or not file_obj:
            return Response(
                {'error': 'Missing file_type or file'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_field_map = {
            'benevity': 'benevity_file',
            'fup': 'fup_file',
            'paypal': 'paypal_file',
            'stripe': 'stripe_file',
            'globalgiving': 'globalgiving_file',
            'bb': 'bb_file',
        }

        field_name = file_field_map.get(file_type)
        if not field_name:
            return Response(
                {'error': 'Invalid file_type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        setattr(analysis, field_name, file_obj)
        analysis.save()

        return Response({
            'message': f'{file_type} file uploaded successfully',
            'file_type': file_type,
            'file_name': file_obj.name,
        })

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Start analysis"""
        analysis = self.get_object()

        if not analysis.all_files_uploaded:
            return Response(
                {'error': 'Not all required files uploaded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if analysis.status == 'processing':
            return Response(
                {'error': 'Analysis already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trigger async task
        process_analysis.delay(analysis.id)

        analysis.status = 'processing'
        analysis.started_at = timezone.now()
        analysis.save()

        return Response({
            'message': 'Analysis started',
            'session_id': analysis.session_id,
        })

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get analysis results"""
        analysis = self.get_object()

        if not analysis.is_complete:
            return Response({
                'status': analysis.status,
                'message': 'Analysis not yet complete',
            })

        donors = UnmatchedDonor.objects.filter(analysis=analysis)
        serializer = UnmatchedDonorSerializer(donors, many=True)

        return Response({
            'status': 'completed',
            'summary': analysis.summary,
            'source_breakdown': analysis.source_breakdown,
            'total_unmatched': analysis.unmatched_donors,
            'donors': serializer.data,
        })

    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Export results as CSV"""
        analysis = self.get_object()

        if not analysis.is_complete:
            return Response(
                {'error': 'Analysis not yet complete'},
                status=status.HTTP_400_BAD_REQUEST
            )

        import csv
        from io import StringIO

        donors = UnmatchedDonor.objects.filter(analysis=analysis)
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ImportID', 'KeyInd', 'Titl1', 'FirstName', 'MidName', 'LastName',
            'OrgName', 'PrimAddID', 'PrimSalID', 'AddrImpID', 'PrefAddr',
            'AddrType', 'AddrLines', 'AddrCity', 'AddrState', 'AddrZIP',
            'PhoneImpID', 'PhoneNum', 'PhoneType', 'PhoneImpID.1',
            'PhoneNum.1', 'PhoneType.1', 'Source'
        ])

        # Write data
        for i, donor in enumerate(donors, start=1000):
            writer.writerow([
                f'{i}', 'I', '', donor.first_name, '', donor.last_name,
                '', '', '', f'A{i}', 'Yes', 'Home', donor.address,
                donor.city, donor.state, donor.zip_code, f'P{i}',
                donor.phone, 'Home' if donor.phone else '', f'P{i+1000}',
                donor.email, 'Email', donor.source
            ])

        # Return as file
        response = Response(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="unmatched_donors_{analysis.session_id}.csv"'
        return response


@login_required
def analysis_list(request):
    """List all analysis sessions"""
    sessions = AnalysisSession.objects.filter(user=request.user)
    return render(request, 'analyzer/analysis_list.html', {
        'sessions': sessions,
    })


@login_required
def analysis_detail(request, session_id):
    """Analysis detail page"""
    analysis = get_object_or_404(AnalysisSession, session_id=session_id, user=request.user)
    donors = UnmatchedDonor.objects.filter(analysis=analysis)

    return render(request, 'analyzer/analysis_detail.html', {
        'analysis': analysis,
        'donors': donors,
        'total_donors': donors.count(),
    })


@login_required
@require_http_methods(["POST"])
def upload_file(request):
    """Handle file upload"""
    session_id = request.POST.get('session_id')
    file_type = request.POST.get('file_type')
    file_obj = request.FILES.get('file')

    try:
        analysis = AnalysisSession.objects.get(session_id=session_id, user=request.user)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)

    file_field_map = {
        'benevity': 'benevity_file',
        'fup': 'fup_file',
        'paypal': 'paypal_file',
        'stripe': 'stripe_file',
        'globalgiving': 'globalgiving_file',
        'bb': 'bb_file',
    }

    field_name = file_field_map.get(file_type)
    if not field_name:
        return JsonResponse({'error': 'Invalid file type'}, status=400)

    setattr(analysis, field_name, file_obj)
    analysis.save()

    return JsonResponse({
        'success': True,
        'message': f'{file_type} uploaded successfully',
        'file_name': file_obj.name,
        'file_size': file_obj.size,
    })


@login_required
@require_http_methods(["POST"])
def start_analysis(request):
    """Start analysis"""
    session_id = request.POST.get('session_id')

    try:
        analysis = AnalysisSession.objects.get(session_id=session_id, user=request.user)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)

    if not analysis.all_files_uploaded:
        return JsonResponse({'error': 'Not all files uploaded'}, status=400)

    # Start async task
    process_analysis.delay(analysis.id)

    analysis.status = 'processing'
    analysis.started_at = timezone.now()
    analysis.save()

    return JsonResponse({
        'success': True,
        'message': 'Analysis started',
    })


@login_required
def download_results(request, session_id):
    """Download results as CSV"""
    analysis = get_object_or_404(AnalysisSession, session_id=session_id, user=request.user)

    if not analysis.is_complete:
        messages.error(request, 'Analysis not yet complete')
        return redirect('analysis_detail', session_id=session_id)

    import csv
    from io import StringIO
    from django.http import HttpResponse

    donors = UnmatchedDonor.objects.filter(analysis=analysis)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="unmatched_donors_{session_id}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ImportID', 'KeyInd', 'Titl1', 'FirstName', 'MidName', 'LastName',
        'OrgName', 'PrimAddID', 'PrimSalID', 'AddrImpID', 'PrefAddr',
        'AddrType', 'AddrLines', 'AddrCity', 'AddrState', 'AddrZIP',
        'PhoneImpID', 'PhoneNum', 'PhoneType', 'PhoneImpID.1',
        'PhoneNum.1', 'PhoneType.1'
    ])

    for i, donor in enumerate(donors, start=1000):
        writer.writerow([
            f'{i}', 'I', '', donor.first_name, '', donor.last_name,
            '', '', '', f'A{i}', 'Yes', 'Home', donor.address,
            donor.city, donor.state, donor.zip_code, f'P{i}',
            donor.phone, 'Home' if donor.phone else '', f'P{i+1000}',
            donor.email, 'Email'
        ])

    return response
