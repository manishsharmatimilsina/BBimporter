from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
import tempfile
import os
import csv
from .utils import analyze_donors


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

    for i, donor in enumerate(data.get('unmatched_donors_list', [])):
        row = [
            f"13025-{i+1}",  # ImportID
            'I',  # KeyInd
            '',  # Titl1
            donor['first_name'],  # FirstName
            '',  # MidName
            donor['last_name'],  # LastName
            '',  # OrgName
            '',  # PrimAddID
            '',  # PrimSalID
            f"A{1000 + i}",  # AddrImpID
            'Yes',  # PrefAddr
            'Home',  # AddrType
            donor['address'],  # AddrLines
            donor['city'],  # AddrCity
            donor['state'],  # AddrState
            donor['zip'],  # AddrZIP
            f"P{1000 + i}" if donor['phone'] else '',  # PhoneImpID
            donor['phone'],  # PhoneNum
            'Home' if donor['phone'] else '',  # PhoneType
            f"P{2000 + i}",  # PhoneImpID1
            donor['email'],  # PhoneNum1
            'Email'  # PhoneType1
        ]
        writer.writerow(row)

    return response
