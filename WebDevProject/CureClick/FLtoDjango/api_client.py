import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = 'http://localhost:5000/api'

class APIClient:
    
    def __init__(self, token=None):
        self.token = token
        self.headers = {
            'Content-Type': 'application/json'
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    def signup(self, username, email, password, full_name):
        """Register a new user"""
        url = f"{API_BASE_URL}/auth/signup"
        payload = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name
        }
        
        logger.info(f"Sending signup request for user: {username}, email: {email}")
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            logger.info(f"Signup response status: {response.status_code}")
            
            if response.status_code not in (200, 201):
                try:
                    error_data = response.json()
                    logger.error(f"Signup error: {error_data}")
                except:
                    logger.error(f"Signup error (non-JSON): {response.text}")
            
            return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Exception during signup: {str(e)}")
            return {"error": str(e)}, 500
    
    def login(self, username, password):
        """Login a user and get authentication token"""
        url = f"{API_BASE_URL}/auth/login"
        payload = {
            'username': username,
            'password': password
        }
        
        logger.info(f"Sending login request for user: {username}")
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            logger.info(f"Login response status: {response.status_code}")
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    logger.error(f"Login error: {error_data}")
                except:
                    logger.error(f"Login error (non-JSON): {response.text}")
            
            return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Exception during login: {str(e)}")
            return {"error": str(e)}, 500
    
    def get_doctors(self):
        """Get all doctors"""
        url = f"{API_BASE_URL}/doctors"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code
    
    def get_doctor(self, doctor_id):
        """Get a specific doctor"""
        url = f"{API_BASE_URL}/doctors/{doctor_id}"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code
    
    def get_consultation_types(self):
        """Get all consultation types"""
        url = f"{API_BASE_URL}/consultation-types"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code
    
    def get_user_bookings(self, user_id):
        """Get all bookings for a user"""
        url = f"{API_BASE_URL}/user-bookings"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code
    
    def create_booking(self, user_id, booking_data):
        """Create a new booking for the user"""
        url = f"{API_BASE_URL}/bookings"
        
        if user_id:
            url = f"{API_BASE_URL}/user-bookings"
        
        # Create a copy of the data to avoid modifying the original
        modified_data = booking_data.copy()
        
        # Make sure service_id is correctly mapped to consultation_type_id
        if 'service_id' in modified_data and 'consultation_type_id' not in modified_data:
            modified_data['consultation_type_id'] = modified_data['service_id']
        
        # Remove service_id as the API expects consultation_type_id
        if 'service_id' in modified_data:
            del modified_data['service_id']
        
        # Print debug info
        print(f"Creating booking with URL: {url}")
        print(f"Booking data: {modified_data}")
        
        response = requests.post(url, json=modified_data, headers=self.headers)
        
        print(f"Booking creation response: {response.status_code}")
        try:
            print(f"Response JSON: {response.json()}")
        except:
            print(f"Response text: {response.text}")
        
        try:
            return response.json(), response.status_code
        except ValueError:
            return {"error": "Invalid response from server"}, response.status_code
    
    def get_booking(self, booking_id):
        """Get a specific booking"""
        url = f"{API_BASE_URL}/bookings/{booking_id}"
        response = requests.get(url, headers=self.headers)
        return response.json(), response.status_code
    
    def update_booking(self, booking_id, data):
        """Update a booking"""
        url = f"{API_BASE_URL}/bookings/{booking_id}"
        response = requests.put(url, json=data, headers=self.headers)
        return response.json(), response.status_code
    
    def cancel_booking(self, booking_id):
        """
        Cancel a booking by setting its status to 'cancelled'.
        This uses the DELETE endpoint, but the API actually updates the status rather than deleting the record.
        """
        url = f"{API_BASE_URL}/bookings/{booking_id}"
        print(f"Sending DELETE request to {url}")
        print(f"Using headers: {self.headers}")
        
        try:
            response = requests.delete(url, headers=self.headers)
            print(f"Got response status code: {response.status_code}")
            
            # Try to parse response as JSON
            try:
                result = response.json()
                print(f"Response body: {result}")
                return result, response.status_code
            except ValueError:
                # If response is not JSON, return raw content
                print(f"Non-JSON response: {response.text}")
                return {"message": response.text}, response.status_code
        except Exception as e:
            print(f"Error making DELETE request: {str(e)}")
            return {"error": str(e)}, 500
    
    def get_doctor_dashboard_data(self, doctor_id, date=None):
        """Get dashboard data for a doctor"""
        url = f"{API_BASE_URL}/doctor-dashboard/{doctor_id}"
        
        params = {}
        if date:
            params['date'] = date
            
        response = requests.get(url, headers=self.headers, params=params)
        return response.json(), response.status_code 
