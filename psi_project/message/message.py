import struct


# Define action constants.
ASK_IF_FILE_EXISTS  = 10
ANSWER_FILE_EXISTS  = 20
START_DOWNLOADING   = 30
CONFIRMATION        = 40
REVOKE              = 50
ACTION_CODES = [ASK_IF_FILE_EXISTS, ANSWER_FILE_EXISTS, START_DOWNLOADING, CONFIRMATION, REVOKE]

# Define status constants.
NOT_APPLICABLE      = 1
ACCEPT              = 200
FILE_EXISTS         = 201
FILE_NOT_FOUND      = 404
BAD_REQUEST         = 400
UPLOAD_CANCELED     = 202
STATUS_CODES = [NOT_APPLICABLE, ACCEPT, FILE_EXISTS, FILE_NOT_FOUND, UPLOAD_CANCELED]



class Message():

    def __init__(self, actionCode: int, status: int, details: str=""):
        self.actionCode = actionCode
        self.status = status
        self.detailsLength = len(details)
        self.details = details
    
    def show_message(self):
        print('actionCode: {}'.format(self.actionCode))
        print('status: {}'.format(self.status))
        print('detailsLength: {}'.format(self.detailsLength))
        print('details: {}\n'.format(self.details))    
    
    def message_to_bytes(self):
        return struct.pack('!hhl40s', self.actionCode, self.status, self.detailsLength, bytes(self.details, 'utf-8'))    
    
    @staticmethod
    def bytes_to_message(message):   
        data = struct.unpack('!hhl40s', message)
        return Message(data[0], data[1], data[3].decode('utf-8').rstrip('\x00'))
    
    @staticmethod
    def print_message(message):
        data = struct.unpack('!hhl40s', message)
        print('actionCode: {}'.format(data[0]))
        print('status: {}'.format(data[1]))
        print('detailsLength: {}'.format(data[2]))
        print('details: {}\n'.format(data[3].decode('utf-8')))
