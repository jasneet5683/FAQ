import functions_framework
from google.cloud import aiplatform
import json
from flask import jsonify, request

# Initialize Vertex AI
aiplatform.init(project="axial-yen-479414-s2", location="us-central1")

@functions_framework.http
def call_agent(request_obj):
    """
    Cloud Run Function with CORS support
    """
    
    # Handle CORS preflight
    if request_obj.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
        }
        return ('', 204, headers)
    
    # Set CORS headers for all responses
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    try:
        # Handle POST requests
        if request_obj.method == 'POST':
            request_json = request_obj.get_json()
            query = request_json.get('query')
            agent_type = request_json.get('agent_type')
            
            if not query or not agent_type:
                return jsonify({
                    'error': 'Missing query or agent_type',
                    'success': False
                }), 400, headers
            
            # Map agent types to display names
            agent_configs = {
                'etisalat': 'etisalat-agent',
                'batelco': 'batelco-agent'
            }
            
            agent_name = agent_configs.get(agent_type.lower())
            if not agent_name:
                return jsonify({
                    'error': f'Invalid agent_type: {agent_type}',
                    'success': False
                }), 400, headers
            
            # Call Vertex AI Agent
            result = call_vertex_ai_agent(query, agent_name)
            
            return jsonify({
                'success': True,
                'query': query,
                'agent_type': agent_type,
                'result': result
            }), 200, headers
        
        else:
            return jsonify({
                'error': f'Method {request_obj.method} not allowed',
                'success': False
            }), 405, headers
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500, headers


def call_vertex_ai_agent(query, agent_display_name):
    """Call Vertex AI Agent"""
    try:
        # List agents to find matching one
        agents = aiplatform.Agent.list(
            filter=f'displayName="{agent_display_name}"'
        )
        
        if not agents:
            raise ValueError(f"Agent '{agent_display_name}' not found")
        
        agent = agents[0]
        
        # Generate response from agent
        response = agent.generate_response(input=query, stream=False)
        
        # Extract text from response
        result = response.text if hasattr(response, 'text') else str(response)
        
        return result
    
    except Exception as e:
        raise Exception(f"Error calling agent '{agent_display_name}': {str(e)}")
