from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from tornado.httpclient import HTTPClient
import unittest
import urllib

from df import Application


class VersionTestCase(AsyncHTTPTestCase):

   def get_app(self):
       return Application()


   def test_beforerevert(self):
       response = self.fetch('/note/6b364d3d/log')
       #assume that before reverting the version number is 3
       self.assertIn("#2", response.body)

   def test_afterrevert(self):
       post_data = { 'username': 'alex', 'password': 'alex' }
       body = urllib.urlencode(post_data)
       http_client = HTTPClient()
       response = http_client.fetch(
               'http://18zhou.com/login',
               method='POST',
               headers=None, 
               body=body,
               )
       post_data = { 'version': 1 }
       body = urllib.urlencode(post_data)
       response = http_client.fetch(
               'http://18zhou.com/note/6b364d3d/log', 
               method='POST', 
               headers={'Cookie':response.headers['Set-Cookie']}, 
               body=body
               ) 
       response = self.fetch('/note/6b364d3d/log')
       after reverting,the version number must be less than 3
       self.assertIn("#2", response.body)

if __name__ == '__main__': 
    unittest.main() 
