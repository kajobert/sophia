import httpx
import json
from typing import Optional, Dict, Any

class HttpClientTools:
    """
    A class to provide tools for making HTTP requests.
    """

    def send_http_request(self, method: str, url: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends an HTTP request to the specified URL.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
            url (str): The URL to send the request to.
            json_body (Optional[Dict[str, Any]]): A JSON serializable dictionary to send as the request body.

        Returns:
            Dict[str, Any]: A dictionary containing the status code and the JSON response body.
        """
        try:
            with httpx.Client() as client:
                response = client.request(method.upper(), url, json=json_body, timeout=30.0)

                response_body = {}
                try:
                    # Attempt to parse the response as JSON
                    response_body = response.json()
                except json.JSONDecodeError:
                    # If parsing fails, use the raw text content
                    response_body = {"raw_content": response.text}

                return {
                    "status_code": response.status_code,
                    "body": response_body,
                }
        except httpx.RequestError as e:
            return {
                "status_code": 500,
                "body": {"error": f"An HTTP request error occurred: {e.__class__.__name__}", "details": str(e)},
            }
        except Exception as e:
            return {
                "status_code": 500,
                "body": {"error": f"An unexpected error occurred: {e.__class__.__name__}", "details": str(e)},
            }