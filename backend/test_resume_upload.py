"""
Test script to verify resume upload endpoint
"""
import requests
import json

# First, login to get a token
login_url = "http://localhost:5000/api/auth/login"
login_data = {
    "email": "test@example.com",
    "password": "password123"
}

print("1. Testing login...")
try:
    response = requests.post(login_url, json=login_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
    
    if response.status_code == 200:
        token = response.json().get('token')
        print(f"   ✓ Got token: {token[:20]}...")
        
        # Now test resume upload with a dummy PDF
        print("\n2. Testing resume upload...")
        upload_url = "http://localhost:5000/api/ai/resume/upload"
        
        # Create a simple test PDF content
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Resume) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000317 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n408\n%%EOF"
        
        files = {'resume': ('test_resume.pdf', test_pdf_content, 'application/pdf')}
        data = {'job_description': 'Software Engineer'}
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(upload_url, files=files, data=data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("   ✓ Resume upload successful!")
        else:
            print(f"   ✗ Resume upload failed!")
    else:
        print("   ✗ Login failed!")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
