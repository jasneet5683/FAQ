import functions_framework
from google.cloud import aiplatform
import json
import re
from flask import jsonify
from flask_cors import cross_origin

# Initialize Vertex AI
aiplatform.init(project="YOUR_PROJECT_ID", location="us-central1")

@functions_framework.http
@cross_origin()
def call_agent(request):
    """
    HTTP Cloud Function to call Vertex AI Agent and return filtered results
    """
    
    # Enable CORS for browser requests
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    
    try:
        # Parse request
        request_json = request.get_json()
        query = request_json.get('query')
        agent_type = request_json.get('agent_type')
        
        if not query or not agent_type:
            return jsonify({'error': 'Missing query or agent_type'}), 400
        
        # Map agent types to their config IDs
        agent_configs = {
            'etisalat': {
                'agent_id': '1e76eb02-a1a3-4268-a49d-b3230c804847',
                'display_name': 'etisalat-agent'
            },
            'batelco': {
                'agent_id': '38c515ce-7666-4779-99cd-db23a2756e9d',
                'display_name': 'batelco-agent'
            }
        }
        
        config = agent_configs.get(agent_type.lower())
        if not config:
            return jsonify({'error': 'Invalid agent_type'}), 400
        
        # Call Vertex AI Agent
        agent_response = call_vertex_ai_agent(query, config['display_name'])
        
        # Filter and clean response
        cleaned_result = clean_agent_response(agent_response)
        
        return jsonify({
            'success': True,
            'query': query,
            'agent_type': agent_type,
            'result': cleaned_result
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


def call_vertex_ai_agent(query, agent_display_name):
    """
    Call Vertex AI Agent with user query
    """
    try:
        agents = aiplatform.Agent.list(
            filter=f'displayName="{agent_display_name}"'
        )
        
        if not agents:
            raise ValueError(f"Agent '{agent_display_name}' not found")
        
        agent = agents[0]
        
        response = agent.generate_response(
            input=query,
            stream=False
        )
        
        return response.text if hasattr(response, 'text') else str(response)
    
    except Exception as e:
        raise Exception(f"Error calling agent: {str(e)}")


def clean_agent_response(raw_response):
    """
    Remove document sources, citations, and metadata from agent response
    """
    
    patterns_to_remove = [
        r'(?i)(source|document|citation|reference|pdf|url).*?(?=\n|$)',
        r'(?i)$$source.*?$$',
        r'(?i)$$source.*?$$',
        r'(?i)retrieved from.*?(?=\n|$)',
        r'(?i)document.*?(?=\n|$)',
    ]
    
    cleaned = raw_response
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned)
    
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())
    cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
    
    return cleaned.strip()
