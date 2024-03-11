"""Provide an interface to access the Lucullus REST API with python
commands."""

import requests
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
import json
from lucullus_rest.utils import dictionaries_to_df
import warnings
import os
from ipaddress import ip_address

rest_url = "http://XXX.XXX.XXX.XXX:8080/lpims/rest/v1/"

try:
    ip_address(rest_url.split("http://")[1].split(":8080")[0])
except ValueError:
    ValueError("The IP adress defined in the core.py file seems to be not valid. Change the IP adress to the IP adress of your server.")

unattendedRequest = "?unattendedRequest=true"

def get_name_to_id_dict(type, auth):
    """Create dictionary that takes names as keys and IDs 
    as values.
    
    Parameters
    ----------
    type : {"ports", "processes", "reactors", "attributedefinitions"}
        String of type of dictionary.
    auth : tuple
        Tuple of username and password.
        
    Returns
    -------
        * Dictionary that takes port names (str) as keys
            and port IDs as values.
    """
    response = requests.get(rest_url+type, auth=auth)
    id_dict = dict()
    if response.status_code == 200:
        json = response.json()
        [id_dict.update({port[u"name"]:port[u"id"]}) for port in json["data"]]
    else:
        raise Exception("Status code of request response was {}.".format(response.status_code))
    return id_dict

def get_process_id(process, auth):
    """Get process id from process name.

    Parameters
    ----------
    process : str or int
        If str then it returns the process ID
        corresponding to the process name, if int just return
        process.
    auth : tuple
        Tuple of username and password.

    Returns
    -------
    process_id : int
        Int ID of lucullus process
    """

    if type(process) == str:
        response = requests.get(rest_url+"processes?name={}".format(process), auth=auth)
        if response.status_code == 200:
            json = response.json()
            process_id = json["data"][0]["id"]
        else:
            raise Exception("Status code of request response was {}.".format(response.status_code))
    elif type(process) == int:
        process_id = process
    return process_id

def get_startTimestamp(process, auth):
    process = get_process_id(process, auth)
    response = requests.get(rest_url+"processes/{}".format(process), auth=auth)
    if response.status_code == 200:
        json = response.json()
        startTimestamp = json["data"]["startTimestamp"]
    else:
        raise Exception("Status code of request response was {}.".format(response.status_code))
    return startTimestamp

def get_port_id(port, auth):
    """Get port id from port name.

    Parameters
    ----------
    port: str or int
        If str then it returns the port ID
        corresponding to the process name, if int just returns
        port.
    auth : tuple
        Tuple of username and password.

    Returns
    -------
    port_id : int
        Int ID of lucullus port.
    """

    if type(port) == str:
        response = requests.get(rest_url+"ports?name={}".format(port), auth=auth)
        if response.status_code == 200:
            json = response.json()
            port_id = json["data"][0]["id"]
        else:
            raise Exception("Status code of request response was {}.".format(response.status_code))
    elif type(port) == int:
        port_id = port
    return port_id

def get_signal_id(process, port, auth):
    """Get signal id from process and port name.

    Parameters
    ----------
    process : str or int
        Process name or process ID.
    port: str or int
        Port name or port ID.
    auth : tuple
        Tuple of username and password.

    Returns
    -------
    signal_id : int
        Signal ID of lucullus signal.
    """
    process = get_process_id(process, auth)

    if type(port) == str:
        port = get_port_id(port, auth)
        response = requests.get(rest_url+"signals?processId={}&portId={}".format(process, port), auth=auth)
        if response.status_code == 200:
            json = response.json()
            signal_id = json["data"]["id"]
        else:
            raise Exception("Status code of request response was {}.".format(response.status_code))
    else:
        signal_id = port

    return signal_id

def export_to_df(process, port_names, auth, interval=0, return_device=False, interpolate=False, backfill=False, devices=None):
    """Get pandas dataframe of process data of specified process
    and port names with the process time as index.

    Parameters
    ----------
    process : str or int
        Either process name as string or process name as int.
    port_names : list
        List of strings specifying the port names.
    auth : tuple
        Tuple of user name and password for authentication
    interval : int, default=0
        Interval in seconds for export of signals. If 0, exports
        all datapoints.
    interpolate : str or False, default=False
        Method to interpolate missing signals in the dataframe. 
        Same as method of pd.DataFrame.interpolate. If no
        interpolation is wanted, set it to False
    device : bool, default=False
        If true, also return list of subdevices.
    backfil : bool, default=False
        If true, starting values of columns are backfilled with
        first value of column.
    devices : list of str, default=None
        Devices specified for the port, in case there are duplicate
        port names.
    
    Returns
    -------
    df : pandas DataFrame
        Pandas dataframe with exported ports of process.
    subdevices : list
        Returned if device=True. List of subdevice names.

    Notes
    -----
    In its current state, even if we use interpolation of the 
    signals we might run into the problem of signals being not
    properly aligned to each other. The reason for this is,
    that each signal is interpolated on each own, so if the
    first signals are not aligned, the whole dataframe will 
    be disaligned.
    Additionally, the interval function of Lucullus seems to
    sometimes generate fake values. This is under investigation.

    Examples
    --------
    >>> export_to_df("process", ["pO2", "IO_pO2_control"], auth, interpolate=False, backfill=False)
                pO2  IO_pO2_control
    Time [h]
    0.01       99.9             NaN
    0.02      100.4             0.0
    0.03       98.9             NaN
    0.04       99.5             NaN

    >>> export_to_df("process", ["pO2", "IO_pO2_control"], auth, interpolate=True, backfill=False)
                pO2  IO_pO2_control
    Time [h]
    0.01       99.9             NaN
    0.02      100.4             0.0
    0.03       98.9             0.0
    0.04       99.5             0.0

    >>> export_to_df("process", ["pO2", "IO_pO2_control"], auth, interpolate=True, backfill=True)
                pO2  IO_pO2_control
    Time [h]
    0.01       99.9             0.0
    0.02      100.4             0.0
    0.03       98.9             0.0
    0.04       99.5             0.0
    """

    json = get_signals(process, port_names, auth, interval=interval, devices=devices)
    df = get_df_from_json(json)

    if interpolate:
        # df.set_index(["Time [h]"], inplace=True)
        df.interpolate(method=interpolate, inplace=True)
        # df.reset_index(inplace=True)
    if backfill:
        df.interpolate(method="backfill", inplace=True)

    if return_device:
        devices = [x["device"]["name"] for x in json["data"]]
        return df, devices
    else:
        return df

def get_signals(process, port_names, auth, interval=0, devices=None):
    """Get json file of process data of specified process and port names.

    Parameters
    ----------
    process : str or int
        Either process name as string or process name as int.
    port_names : list
        List of strings specifying the port names.
    auth : tuple
        Tuple of user name and password for authentication.
    interval : int, default=0
        Interval in seconds for interpolation of data.
    devices : list of str, default=None
        Devices specified for the port, in case there are duplicate
        port names.

    Returns
    -------
    json_data : dict
        json file with exported ports of process.
    """
    process = get_process_id(process, auth)
    signal_info = get_process_signal_info(process, auth)
    port_ids = signal_info[[x in port_names for x in signal_info["portName"]]]["portId"].astype("str")
    if devices is None:
        devices = signal_info[[x in port_names for x in signal_info["portName"]]]["deviceId"].astype("str")
    else:
        raise NotImplementedError("Steve (hatr) is sorry...")
    """
    if devices is None:
        signal_ids = signal_info[[x in port_names for x in signal_info["portName"]]]["id"].astype("str")
    else:
        signal_ids = []
        for name, device in zip(port_names, devices):
            signal_id = signal_info[(signal_info["portName"] == name) & (signal_info["deviceName"] == device)]["id"].astype("str").values.tolist()
            signal_ids += signal_id
    response = requests.get(rest_url+"signals?ids={}&interval={}".format(",".join(signal_ids), interval), auth=auth)
    """
    json_data = []
    for p, d in zip(port_ids, devices):
        response = requests.get(rest_url+"signals?processId={}&portId={}&deviceId={}&interval={}".format(process, p, d, interval), auth=auth)
        if response.status_code != 200:
            raise Exception("Status code of request response was {}.".format(response.status_code))
        json_data.append(response.json())
    return json_data

def get_process_signal_info(process, auth):
    """Get pandas dataframe of info of process signals for process.
    
    Parameters
    ----------
    process : str or int
        Either process name as string or process name as int.
    auth : tuple
        Tuple of user name and password for authentication.
    
    Returns
    -------
    process_signals : pandas DataFrame
        Pandas dataframe with basic info of signals associated with process.
    """
    process = get_process_id(process, auth)

    response = requests.get(rest_url+ "signals?processId={}".format(process), auth=auth)
    process_signals = pd.DataFrame(response.json()["data"])

    for column in ["port", "reactor", "device", "subDevice"]:
        port_info = pd.concat([pd.DataFrame(x, index=[idx]) for idx, x in enumerate(process_signals[column].values)])
        process_signals.drop(column, axis="columns", inplace=True)
        port_info.rename(columns={"id":"{}Id".format(column), "name":"{}Name".format(column)}, copy=False, inplace=True)
        process_signals = pd.concat([process_signals, port_info],axis=1)
    
    return process_signals

def get_df_from_json(json_data):
    """Transform json file into df that is of form as one would get from lucullus export.
    
    Parameters
    ----------
    json_data : dict
        List of Json files that is retrieved from signals.
    
    Returns
    -------
    df : pandas DataFrame
        Pandas dataframe with data stored under the port name and \"Time [h]\" as index.
    """
    
    # I know it seems weird to set Time as a columns and then set as index
    # But this makes it easer for the case when there is no data there

    # Yes, rounding the Time to 5 decimal places is weird, but otherwise data
    # from the same timestamp might be misaligned due to rounding errors.
    
    df_list = [
        pd.DataFrame(
            data=x["data"]["values"], columns=["Time [h]", x["data"]["port"]["name"]]
        ).round({"Time [h]":5}).drop_duplicates(subset="Time [h]").set_index("Time [h]")
        for x in json_data
    ]

    df = pd.concat(df_list, axis=1, sort=True)
    # df.index = df.index.astype(float)
    df.index = pd.TimedeltaIndex(df.index.astype(float), unit="h")

    # df.reset_index(inplace=True)
    return df

def get_running_reactors(auth):
    """Get names and process ids of reactors with status "running".
    
    Parameters
    ----------
    auth : tuple
        Tuple of username and password.

    Returns
    -------
    running_reactors : dict
        Dictionary with running reactors as keys and process IDs as values.
    """
    response = requests.get(rest_url+"reactors?running=true", auth=auth)
    data = response.json()["data"]
    running_reactors = {}
    [running_reactors.update({x["name"]: x["process"]["id"]}) for x in data]
    return running_reactors

def get_running_processes(auth):
    """Get names and ids of processes with status "running".
    
    Parameters
    ----------
    auth : tuple
        Tuple of username and password.
    
    Returns
    -------
    running_processes : dict
        Dictionary with running reactors as keys and process IDs as values.
    """
    response = requests.get(rest_url+"processes?running=true", auth=auth)
    data = response.json()["data"]
    running_processes = {}
    [running_processes.update({x["name"]: x["id"]}) for x in data]
    return running_processes

def get_process_state(process, auth, verbose=True):
    """Get the state of the specified process.

    Parameters
    ----------
    process : str or int
        Either process name as string or process name as int.
    auth : tuple
        Tuple of username and password.
    verbose : bool, default=True
        If True, returns the process state as a string, if False,
        returns the process state as an integer.
    
    Returns
    -------
    process_state : str or int
        String/Integer value defining the process state, based on 
        whether verbose is set to True or False.
    """
    process = get_process_id(process, auth)
    response = requests.get(rest_url+"processes/{}".format(process), auth=auth)
    process_state = response.json()["data"]["state"]
    if verbose:
        process_state = response.json()["included"]["processStateCodes"]["name"]
    else:
        process_state = response.json()["data"]["state"]
    return process_state

def get_current_values(reactor_name, port, auth):
    """Get current values of reactor with "reactor_name" and of 
    ports with "ports_id".
    
    Parameters
    ----------
    reactor_name : str
        Name of reactor.
    port : int, str or list of int or list of str
        ID of port or list of IDs of several ports.
    auth : tuple
        Tuple of username and password.
    
    Returns
    -------
    current_values : dict
        Dictionary with port names and time as "Time [h]".
    """
    if isinstance(port, list):
        port_id_str = ",".join([str(get_port_id(id, auth)) for id in port])
    else:
        port_id_str = str(get_port_id(port, auth))
    link = rest_url+"reactors/"+reactor_name+"?currentValues="+port_id_str
    response = requests.get(
        link,
        auth=auth)
    current_values = {}
    if response.status_code == 200:
        data = response.json()["data"]
        current_values.update(
            {"Time [h]": data["process"]["duration"]}
        )
        [current_values.update({x["name"]: x["value"]}) for x in data["process"]["currentValues"]]
    else:
        print("Request failed. Status code", response.status_code)
        
    return current_values

def set_current_values(process, updated_ports, auth):
    """Set current port values of process.

    Parameters
    ----------
    process : id or str
        Either process name or id.
    updated_ports : dict
        Dictionary where the keys are the port_IDs and the values
        the new value to write to this port.
    auth : tuple
        Tuple of username and password.
    
    Returns
    -------
    None
    """
    process = get_process_id(process, auth)
    port_names = list(updated_ports.keys())
    signal_info = get_process_signal_info(process, auth)
    headers={"Content-Type":"application/json"}
    for p in port_names:
        s = signal_info[signal_info["portName"] == p]["id"].values[0]
        link = rest_url+"signals/{}".format(s)
        response = requests.put(link, data=json.dumps({"currentValue": updated_ports[p]}), auth=auth, headers=headers)
        if response.status_code != 200:
            warnings.warn("Status code of request response for updating port '{}' was '{}'. '{}'".format(p, response.status_code, response.text))
    return

def get_attributes(process, auth):
    """Get attributes of process.
    
    Parameters
    ----------
    process : id or str
        Either process name or id.
    auth : tuple
        Tuple of username and password.

    Returns
    -------
    attributes : dict
        Attributes of specified process.
    """
    process = get_process_id(process, auth)

    response = requests.get(rest_url + "processes/{}".format(process), auth=auth)
    attribute_values = response.json()["data"]["attributes"]
    attribute_values = pd.concat([pd.DataFrame(a, index=[idx]) for idx, a in enumerate(attribute_values)])
    attribute_values.set_index("definitionId", drop=True, inplace=True)

    response = requests.get(rest_url + "attributedefinitions?processIds={}".format(process), auth=auth)
    attributes_meta_info = response.json()["data"]
    attributes_meta_info = pd.concat([pd.DataFrame(a, index=[idx]) for idx, a in enumerate(attributes_meta_info)])
    attributes_meta_info.set_index("id", drop=True, inplace=True)

    attributes = {}
    [attributes.update({attributes_meta_info.loc[id, "name"]: attribute_values.loc[id, "value"]}) for id in attribute_values.index.values]
    return attributes

def set_attributes(process, updated_attributes, auth):
    """Set attributes of process.
    
    Parameters
    ----------
    process : id or str
        Either process name or id.
    updated_attributes : dict
        Dictionary where the keys are the attribute IDs and the 
        values the new value to set this attribute to.
    auth : tuple
        Tuple of username and password.

    Returns
    -------
    None
    """

    process = get_process_id(process, auth)
    headers={"Content-Type":"application/json"}
    response = requests.put(rest_url + "processes/{}/attributes".format(process), data=json.dumps(updated_attributes), auth=auth, headers=headers)
    return

def get_media_table(process, auth):
    """Get table of media of process.
    
    Parameters
    ----------
    process : id or str
        Either process name or id.
    auth : tuple
        Tuple of username and password
    
    Returns
    -------
    media_table : pandas DataFrame
        Table containing information on recipes, lots, amounts etc.
    """
    process = get_process_id(process, auth)
    response = requests.get(rest_url + "processes/{}".format(process), auth=auth)
    json_medium_data = response.json()["data"]["medium"]

    # index = list(json_medium_data.keys())

    recipe_id = [x["recipe"]["id"] for x in json_medium_data["feeds"]]
    recipe_name = [x["recipe"]["name"] for x in json_medium_data["feeds"]]
    lot_id = [x["lot"]["id"] if "lot" in x.keys() else None for x in json_medium_data["feeds"]]
    lot_name = [x["lot"]["name"] if "lot" in x.keys() else None for x in json_medium_data["feeds"]]
    lot_productionDate = [x["lot"]["productionDate"] if "productionDate" in x.keys() else None for x in json_medium_data["feeds"]]
    planned = [x["planned"] for x in json_medium_data["feeds"]]
    amount = [x["amount"] for x in json_medium_data["feeds"]]

    media_table = pd.DataFrame(
        # index=index,
        data={
            "recipe_id":recipe_id,
            "recipe_name":recipe_name,
            "lot_id":lot_id,
            "lot_name":lot_name,
            "lot_productionDate":lot_productionDate,
            "planned":planned,
            "amount":amount}
    )
    return media_table

def get_recipe_table(recipe, auth):
    """Get table for a specific recipe containing ingrediants, actions, etc.
    
    Paramaters
    ----------
    recipe : string or int
        Name of recipe.
    auth : tuple
        Tuple of user name and password.

    Returns
    -------
    recipe_table : pandas dataframe
        Recipe table showing actions and materials of recipe.
    """

    link = rest_url+"recipes/"+str(recipe)
    response = requests.get(link, auth=auth)
    json_data = response.json()

    action_dict = {}
    [action_dict.update({i["id"]:i["name"]}) for i in json_data["included"]["actions"]]
    ingredient_dict = {np.nan:""}
    [ingredient_dict.update({i["id"]:i["name"]}) for i in json_data["included"]["ingredients"]]
    unit_dict = {np.nan:""}
    [unit_dict.update({i["id"]:i["symbol"]}) for i in json_data["included"]["units"]]

    recipe_table = dictionaries_to_df(json_data["data"]["steps"])
    recipe_table["ingredient"] = ["" if np.isnan(i) else ingredient_dict[i] for i in recipe_table["ingredientId"]]
    recipe_table["unit"] = ["" if np.isnan(i) else unit_dict[i] for i in recipe_table["unitId"]]
    recipe_table["action"] = ["" if np.isnan(i) else action_dict[i] for i in recipe_table["actionId"]]
    return recipe_table

def get_process_attributes(process, auth):
    process = get_process_id(process, auth)
    response = requests.get(rest_url + "processes/{}".format(process), auth=auth)
    json_data = response.json()
    process_attributes = {}
    [
        process_attributes.update(
            {[x["name"] for x in json_data["included"]["attributeDefinitions"] if x["id"] == attribute_val["definitionId"]][0]: attribute_val["value"]}
        )
        for attribute_val in json_data["data"]["attributes"]
    ]
    return process_attributes

class Controller:
    """Class controller that periodically
        1. collects data over Lucullus REST-API,
        2. performs calculations on collected data,
        3. acts on calculations by setting current values
    
    Attributes
        ----------
        process : id or str
            Process name as string or process id as integer
        ports : list
            List of strings of ports to collect in collection 
            step
        auth : tuple
            Tuple of username and pasword for authentication
        calc_fun : function, default None
            A function with two inputs, first one a dataframe with
            the collected data, a second one with the already
            calculated data. Returns a new dataframe to replace
            calculated data.
        output_fun : function, default None
            A function with two inputs, first one a dataframe with
            the collected data, a second one with the already
            calculated data. Returns a dictionary of ports to
            update for process.
        end_condition : function, default None
            A function with two inputs, first one a dataframe with
            the collected data, a second one with the already
            calculated data. Returns True or False whether or not
            the update cycle of the controller should continue or
            not. If is None, will continue indefinetely.
        interp_interval : float, default 0
            Interval in seconds for interpolation of collected data
        update_interval : float, default 300
            Interval in seconds for the amount of time that should
            be waited between continuing the collect, calculate,
            act cycle again. If the time for the cycle is longer
            than the interval, will continue immediately.
        save_path :  string or None, default None
            Path where output should be stored as csv. If None,
            will not save as csv.
        collected_data : pd.DataFrame
            Data that is collected from process.
        attributes : dictionary
            Attributes that are collected from process
        calculated_data : pd.DataFrame
            Data that is calculated from collected data.

    Notes
    -----
    The controller needs the writable ports 'ST_LastUpdate' and 
    'ST_NextUpdate' (datatpye is string) which need to be logged by
    default. Otherwise there will be error messages.
    """

    process = int()
    process_name = ""
    ports = []
    signals = []
    auth = ("", "")

    def __init__(self, process, ports, auth, calc_fun=None, output_fun=None, output_attr_fun=None, end_condition=None, interp_interval=0, update_interval=300, save_path=None,
                 print_progress=True, overwrite=False, historic_processes=None, devices=None):
        """Initialize the Controller class."""
        
        self.devices = devices
        self.ports = ports
        self.auth = auth

        if isinstance(process, str):
            self.process_name = process
            self.process = get_process_id(process, self.auth)
        else:
            raise ValueError("Process should be a string.")
        
        self.calc_fun = calc_fun
        self.output_fun = output_fun
        self.output_attr_fun = output_attr_fun

        if end_condition:
            self.end_condition = end_condition
        else:
            self.end_condition = lambda collected_data, calculated_data: True

        self.interp_interval = interp_interval
        self.update_interval = update_interval

        self.collected_data = pd.DataFrame()
        self.calculated_data = pd.DataFrame()
        self.attributes = {}
        self.overwrite = overwrite
        self._create_save_path(save_path)
        self.print_progress = print_progress

        self._historic_processes = historic_processes
        self._collect_historic_data()
        return
    
    def _process_is_running(self):
        process_state = get_process_state(self.process, self.auth, verbose=True)
        is_running = (process_state == "Running")
        return is_running

    def _collect_historic_data(self):
        historic_data = []
        if isinstance(self._historic_processes, list):
            for p in self._historic_processes:
                historic_data.append(export_to_df(p, self.ports, self.auth))
        elif isinstance(self._historic_processes, str):
            historic_data.append(export_to_df(self._historic_processes, self.ports, self.auth))
        
        if historic_data == []:
            self._historic_data = pd.DataFrame()
        else:
            self._historic_data = pd.concat(historic_data, axis=0)
        return

    def _create_save_path(self, save_path):

        if save_path:
            if self.overwrite:
                file_name = "{}_{}.csv".format(self.process, self.__class__.__name__)
            else:
                t = datetime.now()
                time_string = "{}_{:02.0f}{:02.0f}".format(t.date(), t.hour, t.minute)
                file_name = "{}_{}_{}.csv".format(self.process_name, self.__class__.__name__, time_string)
            
            self.save_path = os.path.join(
                save_path,
                file_name
            )
        else:
            self.save_path = None
        return

    def start_update_cycle(self):
        """Continually perform update in the intervall defined in unpdate_interval."""
        
        time_delta = timedelta(seconds=self.update_interval)
        
        while self.end_condition(self.collected_data, self.calculated_data) and self._process_is_running():
            start_time = datetime.utcnow()
            self.update()
            end_time = datetime.utcnow()
            sleep_time = start_time + time_delta - end_time
            if sleep_time.total_seconds() > 0:
                time.sleep(sleep_time.total_seconds())
        
        if self.print_progress:
            print("Stop critera is met. Stopping update cycle.")
        
        return

    def update(self):
        """Update a single time the whole loop consisting of
            * self.collect_data()
            * self.collect_attributes()
            * self.update_calculations()
            * self.update_ports()
            * self.update_attributes()
        """
        
        try:
            self.collect_data()
            self.collect_attributes()
            self.update_calculations()
            self.update_ports()
            self.update_attributes()
            self.save_data()
        except Exception as e:
            warnings.warn(
                "{}: Exception encountered: {}.\nContinue update cycle...".format(
                    str(datetime.now()), str(e)
                )
            )
        return

    def collect_data(self):
        """Collect data specified by process and ports and write
        them to collected_data as a pandas dataframe."""

        if self.ports != []:

            collected_data = export_to_df(
                self.process,
                self.ports,
                self.auth,
                interval=self.interp_interval,
                devices=self.devices
            )

            self.collected_data = pd.concat([self._historic_data, collected_data], axis=0)

        return

    def collect_attributes(self):
        self.attributes = get_attributes(self.process, self.auth)
        return
    
    def update_calculations(self):
        """Perform calculations by calling the function stored in calc_fun."""

        if self.calc_fun:
            self.calculated_data = self.calc_fun(
                self.collected_data,
                self.calculated_data,
                self.attributes
            )

        return

    def update_ports(self):
        """Update ports based on collected data, attributes, and calculated data by calling 
        output_fun and then update the ports defined in the output."""

        now = datetime.now()
        ports_to_update = {}

        if self.output_fun:
            ports_to_update.update(self.output_fun(
                self.collected_data,
                self.calculated_data,
                self.attributes
            ))
    
        if self.print_progress:
            print(now, ports_to_update)

        ports_to_update.update({
            "ST_LastUpdate": str(now),
            "ST_NextUpdate": str(now + timedelta(seconds=self.update_interval))
        })

        set_current_values(
            self.process,
            ports_to_update,
            self.auth
        )

        return
    
    def update_attributes(self):
        """Update attributes based on collected data, attributes, and calculated data by calling 
        output_fun and then update the ports defined in the output."""

        if self.output_attr_fun:
            attributes_to_update = self.output_attr_fun(
                self.collected_data,
                self.calculated_data,
                self.attributes
            )

            if self.print_progress:
                print(datetime.now(), attributes_to_update)

            set_attributes(
                self.process,
                attributes_to_update,
                self.auth
            )
        
        return

    def save_data(self):
        """Save data as csv-file under path specified in
        save_path attribute."""

        if self.save_path:
            try:
                self.calculated_data.to_csv(
                    self.save_path,
                    index=True
                )
            except Exception as err:
                print(err)
        return
    
    def simulate_performance(self, collected_data):
        """
        
        Parameters
        ----------
        collected_data

        Returns
        -------
        updated_ports
        """
        updated_ports = []

        for index in collected_data.index:
            self.collected_data = collected_data.loc[:index, :]
            self.update_calculations()
            updated_ports.append(
                self.output_fun(self.collected_data, self.calculated_data)
            )
        updated_ports = [pd.DataFrame(p, index=[idx]) for idx, p in zip(collected_data.index, updated_ports)]
        updated_ports = pd.concat(updated_ports, axis=0)
        return updated_ports
    
    def function_test(self):
        ####################################
        print("Testing data collection...")
        self.collect_data()
        print(self.collected_data)

        if input("Continue? [y/n]") in ["n", "N"]:
            exit()

        ####################################
        print("Testing attribute collection...")
        self.collect_attributes()
        print(self.attributes)

        if input("Continue? [y/n]") in ["n", "N"]:
            exit()

        ####################################
        print("Testing calculations...")
        self.update_calculations()
        print(self.calculated_data)

        if input("Continue? [y/n]") in ["n", "N"]:
            exit()

        ####################################
        if self.output_fun:
            print("Testing port outputs...")
            out = self.output_fun(self.collected_data, self.calculated_data, self.attributes)
            print(out)

            if input("Continue? [y/n]") in ["n", "N"]:
                exit()
        else:
            print("No output function to test...")

        ####################################
        if self.output_attr_fun:
            print("Testing attribute outputs...")
            out = self.output_attr_fun(self.collected_data, self.calculated_data, self.attributes)
            print(out)

            if input("Continue? [y/n]") in ["n", "N"]:
                exit()
        else:
            print("Not attribute output function to test...")
        
        ####################################
        print("Testing saving calculations...")
        self.save_data()

        if input("Continue? [y/n]") in ["n", "N"]:
            exit()
        
        return
    
