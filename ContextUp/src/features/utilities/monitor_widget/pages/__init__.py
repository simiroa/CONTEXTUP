"""Pages package for Monitor Widget."""
from .process_page import ProcessListPage
from .disk_page import DiskPage
from .net_page import NetPage
from .server_page import ServerPage

__all__ = ['ProcessListPage', 'DiskPage', 'NetPage', 'ServerPage']
