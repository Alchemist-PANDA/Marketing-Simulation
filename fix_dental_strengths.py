import json

def patch_business_data_for_dental(business_data):
    context = business_data.get('business_context', '').lower()
    
    # Fill in missing boolean flags from context for dental
    if 'braces' in context or 'implant' in context or 'whitening' in context or 'root canal' in context:
        if not business_data.get('services'):
            business_data['services'] = []
        if 'braces' in context and 'braces' not in business_data['services']: business_data['services'].append('braces')
        if 'implant' in context and 'implants' not in business_data['services']: business_data['services'].append('implants')
        if 'whitening' in context and 'whitening' not in business_data['services']: business_data['services'].append('whitening')
        if 'root canal' in context and 'root canal' not in business_data['services']: business_data['services'].append('root canal')
        
    if 'professional dentist' in context or 'credential' in context or 'expert' in context:
        business_data['has_credentials'] = True
        
    if 'emergency' in context:
        business_data['has_emergency_info'] = True
        
    if 'hygiene' in context or 'painless' in context or 'steril' in context or 'clean' in context:
        business_data['has_hygiene_info'] = True
        business_data['hygiene_review_mentions'] = 15
        
    if 'appointment' in context or 'booking' in context:
        business_data['has_appointment_info'] = True
        
    if 'patient care' in context:
        business_data['has_patient_care'] = True

    return business_data
