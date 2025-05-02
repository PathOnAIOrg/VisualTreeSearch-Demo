from fastapi import Response
from app.api.services.hello_service import HelloService

class HelloController:
    def __init__(self):
        self.hello_service = HelloService()
        
    def get_hello(self):
        data = self.hello_service.get_hello_data()
        return data