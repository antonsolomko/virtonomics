def __init__(self, server, **kwargs):
    for k, v in kwargs.items():
        setattr(self, k, v)
    self.server = server
    self.domain_ext = self.domain + '/' + self.server + '/main/'
    api_url_prefix = '%s/api/%s/main/' % (self.domain, self.server)
    for key in self.api:
        self.api[key] = api_url_prefix + self.api[key]