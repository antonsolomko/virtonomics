import requests

def open_session(self):
    """Open requests session and login to the game"""
    
    self.session = requests.Session()
    url = '%s/%s/main/user/login' % (self.domain, self.server)
    data = {
        'userData[login]': self.user, 
        'userData[password]': self.password
        }
    self.session.post(url, data=data)
    return self.session