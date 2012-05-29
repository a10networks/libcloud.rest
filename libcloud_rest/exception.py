# -*- coding:utf-8 -*-
import simplejson as json

class LibcloudRestError(Exception):
    """
    Base class for other Libcloud REST exceptions.
    To use this class inherit from it and define attributes.
    """

    code = 1000
    name = 'UnknownError'
    message = 'An unknown error occurred.'
    http_status_code = 500

    def __init__(self, **kwargs):
        self.message = self.message % kwargs
        super(LibcloudRestError, self).__init__()

    def to_json(self):
        """

        @return:
        """
        data = {'error':
                        {
                        'code': self.code,
                        'name': self.name,
                        'message': self.message,
                        }
        }
        return json.dumps(data)


    def __str__(self):
        return '%d (%s) - %s' % (self.code, self.name, self.message)



class ProviderNotSupportedError(LibcloudRestError):
    code = 1001
    code = 'ProviderNotSupported'
    message = 'Provider %(provider)s does not supported.'
    http_status_code= 400


class InternalError(LibcloudRestError):
    code = 1002
    code = 'InternalError'
    message = 'We encountered an internal error.'
    http_status_code = 500

