import pandas as pd
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


def clean_value(val):
    """Convert NaN/None/empty values to empty string"""
    if pd.isna(val) or val is None:
        return ''
    val_str = str(val).strip()
    if val_str.lower() in ['nan', 'none', '']:
        return ''
    return val_str


def load_and_process_benevity(file_path):
    """Load and process BENEVITY CSV"""
    try:
        df = pd.read_csv(file_path, skiprows=11, dtype=str)
        df = df[~df['Company'].str.contains('Totals|Total', na=False, case=False)]

        donors = []
        for idx, row in df.iterrows():
            first_name = clean_value(row.get('Donor First Name', ''))
            email = clean_value(row.get('Email', '')).lower()
            if first_name and email:
                donors.append({
                    'first_name': first_name,
                    'last_name': clean_value(row.get('Donor Last Name', '')),
                    'email': email,
                    'address': clean_value(row.get('Address', '')),
                    'city': clean_value(row.get('City', '')),
                    'state': clean_value(row.get('State/Province', '')),
                    'zip': clean_value(row.get('Postal Code', '')),
                    'phone': '',
                    'source': 'benevity'
                })
        return donors
    except Exception as e:
        logger.error(f"Error processing BENEVITY: {e}")
        return []


def load_and_process_fup(file_path):
    """Load and process FUP RAW CSV"""
    try:
        df = pd.read_csv(file_path)
        df = df[df['Donation Status'] != 'Failed']

        donors = []
        for idx, row in df.iterrows():
            if pd.isna(row.get('Supporter Email')):
                continue
            first_name = clean_value(row.get('Supporter First Name', ''))
            last_name = clean_value(row.get('Supporter Last Name', ''))

            if not first_name and not last_name:
                continue

            donors.append({
                'first_name': first_name,
                'last_name': last_name,
                'email': clean_value(row.get('Supporter Email', '')).lower(),
                'address': clean_value(row.get('Mailing Address Line 1', '')),
                'city': clean_value(row.get('Mailing City', '')),
                'state': clean_value(row.get('Mailing State/Region', '')),
                'zip': clean_value(row.get('Mailing Zip/Postal', '')),
                'phone': clean_value(row.get('Phone Number', '')),
                'source': 'fup'
            })
        return donors
    except Exception as e:
        logger.error(f"Error processing FUP: {e}")
        return []


def load_and_process_paypal(file_path):
    """Load and process PAYPAL RAW CSV"""
    try:
        df = pd.read_csv(file_path)
        df = df[df['Status'] != 'Failed']

        donors = []
        for idx, row in df.iterrows():
            if pd.isna(row.get('From Email Address')):
                continue

            name = clean_value(row.get('Name', ''))
            if not name:
                continue

            name_parts = name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            donors.append({
                'first_name': first_name,
                'last_name': last_name,
                'email': clean_value(row.get('From Email Address', '')).lower(),
                'address': clean_value(row.get('Address Line 1', '')),
                'city': clean_value(row.get('Town/City', '')),
                'state': clean_value(row.get('State/Province/Region/County/Territory/Prefecture/Republic', '')),
                'zip': clean_value(row.get('Zip/Postal Code', '')),
                'phone': clean_value(row.get('Contact Phone Number', '')),
                'source': 'paypal'
            })
        return donors
    except Exception as e:
        logger.error(f"Error processing PAYPAL: {e}")
        return []


def load_and_process_stripe(file_path):
    """Load and process STRIPE RAW CSV"""
    try:
        df = pd.read_csv(file_path)
        df = df[df['Status'] == 'Paid']
        df = df[~df['Description'].str.contains('Fundraise Up', case=False, na=False)]

        donors = []
        for idx, row in df.iterrows():
            if pd.isna(row.get('Customer Email')):
                continue

            name = clean_value(row.get('Customer Description', ''))
            if not name:
                continue

            name_parts = name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            donors.append({
                'first_name': first_name,
                'last_name': last_name,
                'email': clean_value(row.get('Customer Email', '')).lower(),
                'address': '',
                'city': '',
                'state': '',
                'zip': '',
                'phone': '',
                'source': 'stripe'
            })
        return donors
    except Exception as e:
        logger.error(f"Error processing STRIPE: {e}")
        return []


def load_bb_emails(file_path):
    """Load Blackbaud email addresses from both EmailNumber and Email Address columns"""
    try:
        df = pd.read_csv(file_path, encoding='latin1')
        emails = set()

        # Check Email Address Number column
        if 'Email Address Number' in df.columns:
            emails.update(df['Email Address Number'].astype(str).str.lower().dropna())

        # Check Email Address column
        if 'Email Address' in df.columns:
            emails.update(df['Email Address'].astype(str).str.lower().dropna())

        # Remove empty strings and 'nan'
        emails.discard('')
        emails.discard('nan')

        return emails
    except Exception as e:
        logger.error(f"Error loading BB emails: {e}")
        return set()


def analyze_donors(benevity_path, fup_path, paypal_path, stripe_path, bb_path):
    """
    Main analysis function
    Returns: dict with results and unmatched donors list
    """
    # Load BB emails first
    bb_emails = load_bb_emails(bb_path)
    logger.info(f"Loaded {len(bb_emails)} BB emails")

    # Load all donor sources
    all_donors = []
    all_donors.extend(load_and_process_benevity(benevity_path))
    all_donors.extend(load_and_process_fup(fup_path))
    all_donors.extend(load_and_process_paypal(paypal_path))
    all_donors.extend(load_and_process_stripe(stripe_path))

    total_donors = len(all_donors)
    logger.info(f"Loaded {total_donors} total donors from all sources")

    # Deduplicate by email
    donors_by_email = {}
    for donor in all_donors:
        if donor['email'] and donor['email'] not in donors_by_email:
            donors_by_email[donor['email']] = donor

    unique_donors = len(donors_by_email)
    logger.info(f"Found {unique_donors} unique donors after deduplication")

    # Find unmatched
    unmatched = [d for d in donors_by_email.values() if d['email'] not in bb_emails]
    matched = unique_donors - len(unmatched)
    match_rate = (matched / unique_donors * 100) if unique_donors > 0 else 0

    # Get source breakdown
    source_breakdown = {}
    for donor in unmatched:
        source = donor['source']
        source_breakdown[source] = source_breakdown.get(source, 0) + 1

    logger.info(f"Found {len(unmatched)} unmatched donors")
    logger.info(f"Breakdown: {source_breakdown}")

    return {
        'total_donors': total_donors,
        'unique_donors': unique_donors,
        'unmatched': unmatched,
        'matched': matched,
        'match_rate': match_rate,
        'source_breakdown': source_breakdown,
    }
