from celery import shared_task
from django.utils import timezone
from .models import AnalysisSession, UnmatchedDonor, AnalysisLog
from .utils import analyze_donors
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_analysis(analysis_id):
    """Process analysis asynchronously"""
    try:
        analysis = AnalysisSession.objects.get(id=analysis_id)

        # Log start
        AnalysisLog.objects.create(
            analysis=analysis,
            level='info',
            message='Analysis started'
        )

        # Get file paths
        if not all([
            analysis.benevity_file,
            analysis.fup_file,
            analysis.paypal_file,
            analysis.stripe_file,
            analysis.bb_file
        ]):
            raise ValueError("Not all required files are present")

        # Run analysis
        AnalysisLog.objects.create(
            analysis=analysis,
            level='info',
            message='Processing files...'
        )

        results = analyze_donors(
            benevity_path=analysis.benevity_file.path,
            fup_path=analysis.fup_file.path,
            paypal_path=analysis.paypal_file.path,
            stripe_path=analysis.stripe_file.path,
            bb_path=analysis.bb_file.path,
        )

        # Save results
        analysis.total_donors = results['total_donors']
        analysis.unique_donors = results['unique_donors']
        analysis.unmatched_donors = len(results['unmatched'])
        analysis.matched_donors = results['matched']
        analysis.match_rate = results['match_rate']
        analysis.source_breakdown = results['source_breakdown']
        analysis.summary = {
            'total_donors': results['total_donors'],
            'unique_donors': results['unique_donors'],
            'unmatched_donors': len(results['unmatched']),
            'matched_donors': results['matched'],
            'match_rate': round(results['match_rate'], 2),
        }

        # Create donor records
        AnalysisLog.objects.create(
            analysis=analysis,
            level='info',
            message=f'Creating {len(results["unmatched"])} donor records...'
        )

        for i, donor in enumerate(results['unmatched']):
            UnmatchedDonor.objects.create(
                analysis=analysis,
                first_name=donor['first_name'],
                last_name=donor['last_name'],
                email=donor['email'],
                address=donor.get('address', ''),
                city=donor.get('city', ''),
                state=donor.get('state', ''),
                zip_code=donor.get('zip', ''),
                phone=donor.get('phone', ''),
                source=donor['source'],
                import_id=f'{1000 + i}'
            )

        # Mark as complete
        analysis.status = 'completed'
        analysis.completed_at = timezone.now()
        analysis.save()

        AnalysisLog.objects.create(
            analysis=analysis,
            level='success',
            message=f'Analysis completed successfully. Found {len(results["unmatched"])} unmatched donors.'
        )

        logger.info(f"Analysis {analysis_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing analysis {analysis_id}: {e}")

        try:
            analysis = AnalysisSession.objects.get(id=analysis_id)
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()

            AnalysisLog.objects.create(
                analysis=analysis,
                level='error',
                message=f'Analysis failed: {str(e)}'
            )
        except:
            pass


@shared_task
def cleanup_old_files():
    """Clean up old uploaded files"""
    from datetime import timedelta
    from django.utils import timezone

    cutoff_date = timezone.now() - timedelta(days=30)
    old_sessions = AnalysisSession.objects.filter(created_at__lt=cutoff_date)

    for session in old_sessions:
        # Delete files
        if session.benevity_file:
            session.benevity_file.delete()
        if session.fup_file:
            session.fup_file.delete()
        if session.paypal_file:
            session.paypal_file.delete()
        if session.stripe_file:
            session.stripe_file.delete()
        if session.globalgiving_file:
            session.globalgiving_file.delete()
        if session.bb_file:
            session.bb_file.delete()

        # Delete donor records
        UnmatchedDonor.objects.filter(analysis=session).delete()

        # Delete session
        session.delete()

    logger.info(f"Cleaned up {old_sessions.count()} old analysis sessions")
