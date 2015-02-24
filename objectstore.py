from swiftclient.exceptions import *
import swiftclient
from keystoneclient.v2_0 import client
import hmac
from hashlib import sha1
from time import time

class ObjectStore:
      def __init__(self, KEYSTONE_AUTH_URL, SWIFT_USER, SWIFT_PASS, TENANT_NAME, KEYSTONE_AUTH_VERSION, CONTAINER, SWIFT_CONTAINER_BASE_PATH, SECRET_KEY):
           self.container = CONTAINER
           self.container_base_path = SWIFT_CONTAINER_BASE_PATH
           keystone = client.Client(username=SWIFT_USER, password=SWIFT_PASS, tenant_name=TENANT_NAME, auth_url=KEYSTONE_AUTH_URL)
           self.tenant_id = keystone.auth_tenant_id
           self.secret = SECRET_KEY
           self.swift = swiftclient.client.Connection(auth_version=KEYSTONE_AUTH_VERSION,
                                                user=SWIFT_USER,
                                                key=SWIFT_PASS,
                                                tenant_name=TENANT_NAME,
                                                authurl = KEYSTONE_AUTH_URL)
      def check_container_stats(self,container):
          try:
              if(self.swift.head_container(container)):
                return True              
          except ClientException:
              print "Container not found"
              return False

      def create_container(self,container):
          self.swift.put_container(container)

      def delete_container(self,container):
          try:
              self.swift.delete_container(container)
              return True
          except ClientException:
              return False
          except:
              return False
              
 
      def put_object(self,name,obj):
          self.swift.put_object(self.container,name,obj)
      
      def get_temp_url(self, obj, expire_after):
          method = 'GET'
          expires = int(time() + expire_after*60)
          path = '/v1/AUTH_%s/%s/%s' %(self.tenant_id, self.container,obj)
          key = self.secret
          hmac_body = '%s\n%s\n%s' %(method, expires, path)
          sig = hmac.new(key, hmac_body, sha1).hexdigest()
          s = '{base_path}{path}?temp_url_sig={sig}&temp_url_expires={expires}'
          url = s.format(base_path=self.container_base_path, path=path,sig=sig,expires=expires)
          print url
          return url

