
import tableauserverclient as TSC
import argparse
import os
import sys
import platform
import json
import re
import logging

parser = argparse.ArgumentParser(
    description='The app executes tableau prep flow to refresh hyper file locally and/or publish extract file to tableau server\
        The app uses Tableau prep cli ``https://help.tableau.com/current/prep/en-us/prep_run_commandline.htm`` and \
        Tableau Server Python Client ``https://tableau.github.io/server-client-python/docs/``', usage='python %(prog)s [-h] [-v --version] [-t --flow_path] [-c --credentails] [-e --hyper] [-m --mode] [-p --project] [-n --not_embed] [-l --logging]',)
parser.add_argument('-v', '--version',
                    type=str,
                    default='2020.1',
                    metavar='',
                    help='Tableau Prep version, defaults to 2020.1')

parser.add_argument('-t', '--flow_path',
                    type=str,
                    default=None,
                    metavar='',
                    help='path of tableau prep flow.tfl file')

parser.add_argument('-c', '--credentials',
                    type=str,
                    default=None,
                    metavar='',
                    help='path of credential.json per tableau prep cli specification, must contain `outputConnections` credentails for Tableau server for publishing')

parser.add_argument('-e', '--hyper',
                    type=str,
                    default=None,
                    metavar='',
                    help='extract.hyper file path or name for publishing to server. If output of tableau.prep is not in the same folder as flow.tfl or multple hyper files are in the same folder, hyper_path must be explicitly supplied')
parser.add_argument('-m', '--mode',
                    type=str,
                    default='Overwrite',
                    choices=['Overwrite', 'Append',
                             'CreateNew'],
                    metavar='',
                    help='publish mode for extract.hyper. Use ``Overwrite``, ``CreateNew`` or ``Append`` values, defaults to Overwrite ')
parser.add_argument('-p', '--project',
                    type=str,
                    default='Default',
                    metavar='',
                    help='destination Project (folder) on tableau server for publishing extract.hyper, defaults to Default project')
parser.add_argument('-n', '--not_embed',
                    default=None,
                    action="store_true",
                    help='flag for not embeding credentials in datasource,')
parser.add_argument('-l', '--logging',
                    type=str,
                    default='INFO',
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    metavar='',
                    help='logging level, defaults to INFO. use DEBUG, INFO, WARNING, ERROR, CRITICAL')


args = parser.parse_args()

flow_path = args.flow_path
cred_path = args.credentials
tableau_prep_version = args.version
hyper_path = args.hyper
mode = args.mode.title()

destination_project = args.project
log_level = args.logging.upper()
not_embed = args.not_embed
if not_embed != None:
    embed = False
else:
    embed = True
project = args.project

# args_dict = argparse.Namespace()

logger = logging.getLogger()
if log_level == 'DEBUG':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('Log level set to DEBUG')
elif log_level == 'WARNING':
    logging.basicConfig(level=logging.WARNING)
elif log_level == 'ERROR':
    logging.info(f'log level set to {logger.level}')
elif log_level == 'CRITICAL':
    logging.basicConfig(level=logging.CRITICAL)
else:
    logging.basicConfig(level=logging.INFO)

logging.debug(f'supplied arguemnts are: {args}')


def main():
    # create tableau prep cli script
    if flow_path:
        if os.path.isfile(flow_path):
            shell_command = create_script(flow_path)
            logging.debug(f"command for tableau prep cli: {shell_command}")
    elif hyper_path:
        if os.path.isfile(hyper_path):
            if not os.path.isfile(cred_path):
                sys.exit('please provide either a valid tableau prep.tfl filepath for refreshing extract locally or extract.hyper and server login credetials.json filepath should for publishing to server')
        shell_command = None
    else:
        sys.exit('either a valid tableau prep.tfl filepath for refreshing extract locally or extract.hyper and server login credetials.json filepath should be provided for publishing to server')
    # customize credentials for tableau flow (keep only input credentials, as flow should publish local extract file)
    if cred_path:
        if os.path.isfile(cred_path):
            input_cred, output_cred = __split_cred_file__(cred_path, flow_path)
        else:
            logging.debug(f'credential file path is not valid: {cred_path}')

    else:
        input_cred = output_cred = None

    # execute flow
    if platform.system() == 'Windows':
        script_path = r'C:\Program Files\Tableau\Tableau Prep Builder {version}\scripts'.format(
            version=tableau_prep_version)
        os.chdir(script_path)
        logging.debug(f'running tableau prep script at {os.getcwd()}')

    if shell_command:
        os.system(shell_command)

    # publish extract.hyper
    if cred_path:
        if os.path.isfile(cred_path):
            logging.debug(
                f'arguments: hyper_pth={hyper_path}, cred_path={cred_path}, hyper_path={hyper_path}, mode={mode}, project={project}, embed={embed}')
            publish_hyper(hyper_file=hyper_path, credential_path=cred_path, flow_path=flow_path,
                          mode=mode, project=project, embed=embed)
        else:
            sys.exit(f'{cred_path} filepath is invalid')
    else:
        sys.exit(
            'credentials.json filepath was not provided for publishing extract to server')


def create_script(flow_path, credential_path=None, prep_builder_version='2020.1'):
    """creates command for Tableau Prep-cli for both Mac OS and Windows

    Arguments:
        flow_path {str} -- path to Tebleau Prep.tfl file

    Keyword Arguments:
        credential_path {str} -- path of credential.json for input an output connections (default: {None})
        prep_builder_version {str} -- Tableau Prep version (default: {'2020.1'})

    Returns:
        str -- shell script for executing Tebleau Prep.tfl with Tableau Prep-cli
    """

    if platform.system() == 'Windows':
        script_path = r'C:\Program Files\Tableau\Tableau Prep Builder {version}\scripts'.format(
            version=prep_builder_version)
        if credential_path:
            assert os.path.isfile(flow_path) == True and os.path.isfile(
                credential_path) == True
            windows_script = r'tableau-prep-cli.bat -c "{input_cred}" -t "{flow_path}"'.format(
                input_cred=credential_path, flow_path=flow_path)
        else:
            assert os.path.isfile(flow_path) == True
            windows_script = r'tableau-prep-cli.bat -t "{flow_path}"'.format(
                flow_path=flow_path)
        return windows_script
    else:
        if credential_path:
            assert os.path.isfile(flow_path) == True and os.path.isfile(
                credential_path) == True
            mac_script = f"/Applications/'Tableau Prep Builder {prep_builder_version}.app'/Contents/scripts/./tableau-prep-cli -c {credential_path} -t '{flow_path}'"

        else:
            assert os.path.isfile(flow_path) == True
            mac_script = f"/Applications/'Tableau Prep Builder {prep_builder_version}.app'/Contents/scripts/./tableau-prep-cli -t '{flow_path}'"
        return mac_script


def __split_cred_file__(credential_path, flow_path):
    """creates separate input_cred.json file for tableau prep.tfl for local publishing and output_cred.json for publishing to tableau server

    Arguments:
        credential_path {str}
        flow_path {str}

    Returns:
        tupple -- (input_cred_path , output_cred_path)
    """
    if flow_path:
        project_dir = os.path.dirname(flow_path)
    else:
        project_dir = os.path.dirname(cred_path)
    output_cred_path = os.path.join(
        project_dir, 'tableau_prep_output_cred.json')
    input_cred_path = os.path.join(project_dir, 'tableau_prep_input_cred.json')
    with open(credential_path, 'r') as file:
        credentials = json.load(file)

        if credentials.get('outputConnections'):
            cred = {'outputConnections': credentials.get('outputConnections')}
            with open(output_cred_path, 'w') as output_cred_file:
                json.dump(cred, output_cred_file)
                logging.debug(
                    f'`output_cred.json` for input connections created in project folder `{project_dir}`')
        elif not credentials.get('outputConnections'):
            output_cred_path = None

        if credentials.get('inputConnections'):
            cred = {'inputConnections': credentials.get('inputConnections')}
            with open(input_cred_path, 'w') as input_cred_file:
                json.dump(cred, input_cred_file)
                logging.debug(
                    f'`input_cred.json` for input connections created in project folder `{project_dir}`')
        elif not credentials.get('inputConnections'):
            input_cred_path = None

    return input_cred_path, output_cred_path


def get_files_in_folder(folderpath="./", file_extenion="."):
    """returns filenames in a local folder (sub directories are ignored), filters filepaths by file extension

    Keyword Arguments:
        folderpath {str} -- relative or absolute path of directory (default: {"./"})
        file_extenion {str} -- e.g .py, .ipynb, .txt, .pdf etc (default: all filetype)

    Returns:
        list -- list collection containing matched file names
    """
    if folderpath == "./":
        logging.debug(f"searching in current working dir: {os.getcwd()}")
    else:
        logging.debug(f"searching in {folderpath}")

    if file_extenion == ".":
        file_extenion = file_extenion.lower()
        logging.debug(f"searching for all files in {folderpath}")
    else:
        logging.debug(
            f"searching for files with {file_extenion} extension in {folderpath}")
        file_extenion = file_extenion.lower()+"$"

    from os import listdir
    from os.path import isfile, join
    files = [f for f in listdir(folderpath) if isfile(
        join(folderpath, f)) and re.search(r'{}'.format(file_extenion), f)]
    return files


def publish_hyper(hyper_file, credential_path, flow_path=None, **kwargs):
    """ publishes local extract.hyper file to tableau server, main method is datasources.publish(datasource_item, file_path, mode, connection_credentials=None)
    https://tableau.github.io/server-client-python/docs/api-ref#data-sources

    Arguments:
        hyper_file {str} -- filepath of extract.hyper or .tde to be published
        credential_path {str} -- credential.json file per tableau prep cli specification, must contain `outputConnections` credentails for Tableau server

    Keyword Arguments:
        flow_path {str} -- [description] (default: {None})
        project {str} -- tableau prep folder/project (Defaults: {Defaults})
        mode {str} -- CreateNew|Overwrite|Append (Defaults: Overwrite)
        embed {bool} -- if True, embeds credentails in data source (Defaults: True)
    """
    with open(credential_path, 'r') as file:
        credentials = json.load(file).get('outputConnections')[0]
    server_address = credentials.get('serverUrl')
    username = credentials.get('username')
    password = credentials.get('password')
    logging.info(f"singing into {server_address} as {username}")

    server = TSC.Server(server_address)
    tableau_auth = TSC.TableauAuth(
        username, password, credentials.get('contentUrl'))
    # server.auth.sign_in(tableau_auth)

    logging.debug(f'supplied keyword args: {kwargs}')
    with server.auth.sign_in(tableau_auth):
        assert server.is_signed_in() == True
        if 'project' not in kwargs.keys():
            all_project_items, pagination_item = server.projects.get()
            project_id = [
                project.id for project in all_project_items if project.name == 'Default'][0]
        else:
            all_project_items, pagination_item = server.projects.get()
            project_id = [
                project.id for project in all_project_items if project.name == kwargs.get('project')][0]

        logging.debug(f"project_id for {project} is : {project_id}")

        if not hyper_file:
            if flow_path:
                flow_name = os.path.basename(flow_path)
                project_dir = os.path.dirname(flow_path)
                os.chdir(project_dir)
                hyper_list = get_files_in_folder(
                    folderpath=project_dir, file_extenion="hyper")
                if len(hyper_list) > 1:
                    name = hyper_list[0]
                    logging.warning(
                        f'found more that one hyper files in tableau prep flow folder ``{project_dir}``, publising ``{name}`` to server. explicitly provide hyper_path to publish desired extract file')
                elif len(hyper_list) == 1:
                    name = hyper_list[0]
                else:
                    logging.error(
                        f'no extract.hyper file was found in tableau prep flow folder ``{project_dir}``, check that flow outputs file in hyper format or explicitly provide hyper_path to publish desired extract file')
            else:
                logging.error(
                    f'could not find extract.hyper file to publish, explicitly provide hyper_path to publish desired extract file')
            hyper_filepath = os.path.join(project_dir, name)
        elif os.path.isfile(hyper_file) == True:
            hyper_filepath = hyper_file
            name = os.path.basename(hyper_file)
        else:  # only filename is pass which is in project folder
            name = hyper_file
            hyper_filepath = os.path.join(project_dir, name)

        assert os.path.isfile(hyper_filepath) == True
        logging.info(
            f'publishing extract file ``{hyper_filepath}`` to ``{project}`` project')
        name = name.split('.')[0]  # remove file extension

        if 'mode' in kwargs.keys():
            mode = kwargs.get('mode').title()
            if mode == 'Createnew':
                mode = 'CreateNew'

            if mode == 'Append':
                all_datasources, pagination_item = server.datasources.get()
                if 'name' in kwargs.keys():
                    name = kwargs.get('name')
                datasource_id = [
                    datasource.id for datasource in all_datasources if datasource.name == name][0]
                data_source_item = server.datasources.get_by_id(datasource_id)
                logging.info(f"appending {hyper_filepath} to {name}")
            else:
                data_source_item = TSC.DatasourceItem(
                    project_id=project_id, name=name)
                logging.info(
                    f"publishing {hyper_filepath} as {name} in {mode} mode")

        else:
            mode = 'Overwrite'
            data_source_item = TSC.DatasourceItem(
                project_id=project_id, name=name)
            logging.info(f"publishing {name} in {mode} mode")

            if 'embed' in kwargs.keys():
                embedded_credential = TSC.ConnectionCredentials(
                    username, password, embed=embed, oauth=False)
                server.datasources.publish(
                    data_source_item, hyper_filepath, mode, connection_credentials=embedded_credential)
            else:
                server.datasources.publish(
                    data_source_item, hyper_filepath, mode)
    logging.info(f'{hyper_filepath} was successfully published!')


if __name__ == '__main__':
    main()
