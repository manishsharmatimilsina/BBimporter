from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
import tempfile
import os
import csv
from .utils import analyze_donors, clean_value


def home(request):
    """Home page - upload files and view results"""
    results = None

    if request.method == 'POST':
        files = {
            'benevity': request.FILES.get('benevity'),
            'fup': request.FILES.get('fup'),
            'paypal': request.FILES.get('paypal'),
            'stripe': request.FILES.get('stripe'),
            'globalgiving': request.FILES.get('globalgiving'),
            'bb': request.FILES.get('bb'),
        }

        uploaded_files = {k: v for k, v in files.items() if v}
        if not uploaded_files:
            messages.error(request, 'Please upload at least one file.')
        elif 'bb' not in uploaded_files:
            messages.error(request, 'BB Import file is required for matching.')
        else:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_paths = {}
                    for key, file_obj in uploaded_files.items():
                        file_path = os.path.join(tmpdir, file_obj.name)
                        with open(file_path, 'wb') as f:
                            f.write(file_obj.read())
                        file_paths[key] = file_path

                    analysis = analyze_donors(
                        file_paths.get('benevity'),
                        file_paths.get('fup'),
                        file_paths.get('paypal'),
                        file_paths.get('stripe'),
                        file_paths.get('bb')
                    )

                    results = {
                        'total_donors': analysis['total_donors'],
                        'unique_donors': analysis['unique_donors'],
                        'matched_donors': analysis['matched'],
                        'unmatched_donors': len(analysis['unmatched']),
                        'match_rate': analysis['match_rate'],
                        'source_breakdown': analysis['source_breakdown'],
                        'unmatched_donors_list': [
                            {
                                'name': f"{d['first_name']} {d['last_name']}",
                                'first_name': d['first_name'],
                                'last_name': d['last_name'],
                                'email': d['email'],
                                'address': d['address'],
                                'city': d['city'],
                                'state': d['state'],
                                'zip': d['zip'],
                                'phone': d['phone'],
                                'source': d['source']
                            }
                            for d in analysis['unmatched']
                        ]
                    }
                    request.session['analysis_results'] = results
                    messages.success(request, 'Files processed successfully.')
            except Exception as e:
                messages.error(request, f'Error processing files: {str(e)}')

    return render(request, 'analyzer/home.html', {'results': results})


def download_results(request):
    """Download unmatched donors as CSV in Blackbaud import format"""
    data = request.session.get('analysis_results')
    if not data:
        messages.error(request, 'No results to download.')
        return render(request, 'analyzer/home.html')

    from datetime import datetime
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Unmatched_Donors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)

    headers = [
        'ImportID', 'KeyInd', 'Titl1', 'FirstName', 'MidName', 'LastName',
        'OrgName', 'PrimAddID', 'PrimSalID', 'AddrImpID', 'PrefAddr', 'AddrType',
        'AddrLines', 'AddrCity', 'AddrState', 'AddrZIP', 'PhoneImpID', 'PhoneNum',
        'PhoneType', 'PhoneImpID1', 'PhoneNum1', 'PhoneType1'
    ]
    writer.writerow(headers)

    # Generate date-based ID prefix (MMDDYYYY)
    now = datetime.now()
    date_prefix = now.strftime("%m%d%Y")

    for i, donor in enumerate(data.get('unmatched_donors_list', [])):
        import_id_num = f"{i+1:02d}"  # Zero-padded number (01, 02, etc.)

        row = [
            f"{date_prefix}-{import_id_num}",  # ImportID: 04242026-01
            'I',  # KeyInd
            '',  # Titl1
            clean_value(donor['first_name']),  # FirstName
            '',  # MidName
            clean_value(donor['last_name']),  # LastName
            '',  # OrgName
            '',  # PrimAddID
            '',  # PrimSalID
            f"A{date_prefix}-{import_id_num}",  # AddrImpID: A04242026-01
            'Yes' if clean_value(donor['address']) else '',  # PrefAddr
            'Home' if clean_value(donor['address']) else '',  # AddrType
            clean_value(donor['address']),  # AddrLines
            clean_value(donor['city']),  # AddrCity
            clean_value(donor['state']),  # AddrState
            clean_value(donor['zip']),  # AddrZIP
            f"P{date_prefix}-{import_id_num}" if clean_value(donor['phone']) else '',  # PhoneImpID
            clean_value(donor['phone']),  # PhoneNum
            'Home' if clean_value(donor['phone']) else '',  # PhoneType
            '',  # PhoneImpID1
            '',  # PhoneNum1
            ''  # PhoneType1
        ]
        writer.writerow(row)

    return response
