from mapflow.functional.view.main_dialog import MainDialog


class ProcessingView:
    """
    This class incorporates everything we take responsible for the processing start and cost update

    - readings from the UI elements
    - some checks on the correspondence of UI controls
    - changes in the UI with the processing start(?)
    - display of the finished processings in the table (not yet?)
    """
    def __init__(self, dlg: MainDialog):
        self.dlg = dlg

    @property
    def processing_name(self):
        # this is a sample function, maybe we'll not need it
        return self.dlg.processingName.text()

    @property
    def processing_name_valid(self):
        # this is a sample function, maybe we'll not need it
        return self.processing_name != ""

    def read_processing_start_params(self):
        return {}
