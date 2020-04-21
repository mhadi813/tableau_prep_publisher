# tableau_prep_publisher
The app executes tableau prep flow to refresh extract.hyper file locally and/or publishes extract file to tableau server

Situations in which this app is useful:
  - you don't have access to tableau prep conductor or the server is running on different version
  - you develop tableau prep flow on mac OS and want to refresh the extract file with batch jobs running on windows machine
  - tableau server requires two factor authentication
  - or you want to use service account for publishing extracts to tableau server

# set up:
1) create python virtual environment and install requirements
2) modify flow to output extract file on local machine
3) create batch or shell script to execute tableau_prep_publisher.py in the virtual environment
4) schedule batch job or shell script

# command line arguments:
python tableau_prep_publisher.py --help

### usage: python tableau_prep_publisher.py [-h] [-v --version] [-t --flow_path] [-c --credentails] [-e --hyper] [-m --mode] [-p --project] [-n --not_embed] [-l --logging]

### optional arguments:
  -h, --help           show this help message and exit
  
  -v , --version       Tableau Prep version, defaults to 2020.1
  
  -t , --flow_path     path of tableau prep flow.tfl file
  
  -c , --credentials   path of credential.json per tableau prep cli specification, must contain `outputConnections`                                  credentails for Tableau server for publishing
  
  -e , --hyper         extract.hyper file path or name for publishing to server. If output of tableau.prep is not in the same
                       folder as flow.tfl or multple hyper files are in the same folder, hyper_path must be explicitly                                supplied
                       
  -m , --mode          publish mode for extract.hyper. Use ``Overwrite``, ``CreateNew`` or ``Append`` values, defaults to
                       Overwrite
                       
  -p , --project       destination Project (folder) on tableau server for publishing extract.hyper, defaults to Default                              project
  
  -n, --not_embed      flag for not embeding credentials in datasource
  
  -l , --logging       logging level, defaults to INFO. use DEBUG, INFO, WARNING, ERROR, CRITICAL
