def __del__(self):
    self.quit()


def quit(self):
    """Close any connections if open.
    
    Todo:
        * Does not currently support inheritance.
    """
    
    if 'driver' in self.__dict__:
        self.driver.quit()
    if 'session' in self.__dict__:
        self.session.close()
    if 'conn' in self.__dict__:
        self.conn.close()