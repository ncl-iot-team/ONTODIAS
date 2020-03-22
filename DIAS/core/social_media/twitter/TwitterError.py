

'''
    This from api: twitter source code
'''
class TwitterError(Exception):
    """Base class for Twitter errors"""

    @property
    def message(self):
        '''Returns the first argument used to construct this error.'''
        return self.args[0]