from irods.session import iRODSSession
from irods.exception import DataObjectDoesNotExist
from pathlib import Path
import os


class CyVerseDownloader:

    def __init__(self, username=os.environ.get('CYVERSE_USERNAME'),
                 password=os.environ.get('CYVERSE_PASSWORD'),
                 dest='.'):
        self.username = username
        self.password = password
        self.destination = dest

    def get_conus_data(self, file):
        with iRODSSession(host='data.cyverse.org',
                          port=1247,
                          user=self.username,
                          password=self.password,
                          zone='iplant') as session:
            try:
                obj = session.data_objects.get(file)
                # open(self.Path(file).name, 'wb').write(obj.open().read())
                with open(os.path.join(self.destination, Path(file).name), 'wb') as f:
                    with obj.open() as f_obj:
                        f.write(f_obj.read())
            except DataObjectDoesNotExist:
                print(f'could not locate {file}')