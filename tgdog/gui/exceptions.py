class GUIException(Exception):
    pass


class GUIError(GUIException):
    pass


class ReconstructionError(GUIError):
    pass


class NoWindowError(ReconstructionError):
    pass


class PermissionError(ReconstructionError):
    pass


class StopUserRequestProcessing(GUIException):

    def __init__(self, window, alert=None):
        self.window = window
        self.alert = alert
