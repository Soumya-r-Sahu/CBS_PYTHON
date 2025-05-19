"""
Framework Detection and Compatibility Utilities

This module provides utilities for detecting and supporting different frontend frameworks
that interact with the CBS_PYTHON backend. It helps ensure seamless integration with
Django, React, Angular, Vue.js and other frameworks.
"""

import re
from typing import Dict, Any, Optional, List, Tuple

def detect_framework_from_headers(headers: Dict[str, str]) -> str:
    """
    Detect the frontend framework based on request headers
    
    Args:
        headers: HTTP request headers dictionary
    
    Returns:
        Detected framework name or 'generic' if unknown
    """
    user_agent = headers.get('User-Agent', '').lower()
    
    # Check for framework-specific headers
    if 'X-Django-CSRF-Token' in headers or 'csrftoken' in headers.get('Cookie', ''):
        return 'django'
        
    if 'X-Requested-By' in headers and headers['X-Requested-By'] == 'Angular':
        return 'angular'
        
    # Check user agent for clues
    if 'angular' in user_agent:
        return 'angular'
        
    if 'react' in user_agent:
        return 'react'
        
    if 'vue' in user_agent:
        return 'vue'
        
    # If we have XMLHttpRequest but no specific framework
    if headers.get('X-Requested-With') == 'XMLHttpRequest':
        # This could be any modern framework, return generic AJAX
        return 'ajax'
        
    return 'generic'

def get_framework_specific_config(framework: str) -> Dict[str, Any]:
    """
    Get framework-specific configuration for optimizing compatibility
    
    Args:
        framework: Name of the detected frontend framework
    
    Returns:
        Dictionary with framework-specific configuration
    """
    # Base configuration that works with all frameworks
    config = {
        'content_type': 'application/json',
        'auth_header': 'Authorization',
        'auth_scheme': 'Bearer',
        'supports_cors': True,
        'supports_csrf': False,
        'recommended_libraries': []
    }
    
    # Framework specific overrides
    if framework == 'django':
        config.update({
            'supports_csrf': True,
            'csrf_header': 'X-CSRFToken',
            'csrf_cookie': 'csrftoken',
            'session_cookie': 'sessionid',
            'recommended_libraries': ['requests', 'django-rest-framework']
        })
    elif framework == 'react':
        config.update({
            'recommended_libraries': ['axios', 'fetch-api', '@cbs/react-banking-api'],
            'token_storage': 'localStorage'
        })
    elif framework == 'angular':
        config.update({
            'recommended_libraries': ['@angular/common/http', '@cbs/angular-banking-api'],
            'auth_interceptor': True,
            'token_storage': 'localStorage'
        })
    elif framework == 'vue':
        config.update({
            'recommended_libraries': ['axios', '@cbs/vue-banking-api'],
            'token_storage': 'localStorage'
        })
        
    return config

def get_framework_compatibility_issues(framework: str) -> List[Dict[str, str]]:
    """
    Get known compatibility issues and workarounds for specific frameworks
    
    Args:
        framework: Name of the frontend framework
    
    Returns:
        List of dictionaries with issue and solution information
    """
    issues = []
    
    if framework == 'django':
        issues.append({
            'issue': 'CSRF token validation may fail for AJAX requests',
            'solution': 'Ensure the X-CSRFToken header is included in all POST/PUT/DELETE requests'
        })
    elif framework == 'react':
        issues.append({
            'issue': 'React strict mode causes double API calls during development',
            'solution': 'Use useEffect cleanup or implement request deduplication'
        })
    elif framework == 'angular':
        issues.append({
            'issue': 'HTTP Interceptors may not handle refresh tokens automatically',
            'solution': 'Implement a custom HTTP Interceptor using the provided Angular client library'
        })
    elif framework == 'vue':
        issues.append({
            'issue': 'Vue 2 and Vue 3 require different Axios integration approaches',
            'solution': 'Use the provided Vue client library which works with both Vue versions'
        })
        
    # Common issues for all frameworks
    issues.append({
        'issue': 'CORS preflight requests may fail in some environments',
        'solution': 'Ensure the API server has proper CORS headers configured for your origin'
    })
    
    return issues

def generate_framework_sample_code(framework: str, endpoint: str) -> str:
    """
    Generate sample code for accessing an API endpoint with the specified framework
    
    Args:
        framework: Frontend framework name (django, react, angular, vue)
        endpoint: API endpoint path (e.g., '/api/v1/accounts')
    
    Returns:
        String containing sample code for the specified framework
    """
    base_url = 'http://localhost:5000'
    full_url = f'{base_url}{endpoint}'
    
    if framework == 'django':
        return f'''# Django example using requests
import requests
from django.conf import settings

def get_data_from_api(request):
    headers = {{'Authorization': f"Bearer {{request.session.get('token')}}"}}
    response = requests.get("{full_url}", headers=headers)
    return response.json()
'''
    elif framework == 'react':
        return f'''// React example using @cbs/react-banking-api
import {{ BankingApiClient }} from '@cbs/react-banking-api';

const apiClient = new BankingApiClient({{
  baseUrl: 'http://localhost:5000/api/v1',
  timeout: 30000,
  retryAttempts: 3
}});

// Set token provider
apiClient.tokenProvider = () => localStorage.getItem('jwt_token');

// In your component
const fetchData = async () => {{
  try {{
    const data = await apiClient.getAccounts();
    setAccounts(data);
  }} catch (error) {{
    console.error('Error fetching data:', error);
  }}
}};
'''
    elif framework == 'angular':
        return f'''// Angular example using @cbs/angular-banking-api
import {{ Component, OnInit }} from '@angular/core';
import {{ BankingApiService }} from '@cbs/angular-banking-api';

@Component({{
  selector: 'app-data',
  template: `<div *ngIf="loading">Loading...</div>
             <div *ngIf="accounts">
               <div *ngFor="let account of accounts">
                 {{{{ account.accountNumber }}}}
               </div>
             </div>`
}})
export class DataComponent implements OnInit {{
  accounts: any[] = [];
  loading = true;

  constructor(private bankingApi: BankingApiService) {{}}

  ngOnInit() {{
    this.bankingApi.getAccounts().subscribe(
      data => {{
        this.accounts = data;
        this.loading = false;
      }},
      error => {{
        console.error('Error fetching accounts:', error);
        this.loading = false;
      }}
    );
  }}
}}
'''
    elif framework == 'vue':
        return f'''// Vue 3 example using @cbs/vue-banking-api
<script setup>
import {{ ref, onMounted }} from 'vue';
import {{ useAccounts }} from '@cbs/vue-banking-api/composables';

const {{ accounts, fetchAccounts, isLoading, error }} = useAccounts();

onMounted(() => {{
  fetchAccounts();
}});
</script>

<template>
  <div v-if="isLoading">Loading...</div>
  <div v-else-if="error">Error: {{ error }}</div>
  <div v-else>
    <div v-for="account in accounts" :key="account.id">
      {{ account.accountNumber }}
    </div>
  </div>
</template>
'''
    
    # Generic JavaScript/fetch example as fallback
    return f'''// Generic JavaScript example using fetch
fetch("{full_url}", {{
  method: 'GET',
  headers: {{
    'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
    'Content-Type': 'application/json'
  }}
}})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
'''
