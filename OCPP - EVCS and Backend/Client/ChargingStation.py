import asyncio
import logging
from multiprocessing.dummy import active_children
from pkgutil import iter_modules
from urllib.request import Request

from datetime import datetime
import urllib
import requests

import websockets
from ocpp.routing import on, after

from ocpp.v201 import call, call_result
from ocpp.v201 import ChargePoint as cp
from ocpp.v201.enums import (
    Action,
    ChargingProfileStatus,
    FirmwareStatusType,
    UpdateFirmwareStatusType,
    DisplayMessageStatusType,
    UnitOfMeasureType,
    MeasurandType,
    ChargingProfileStatus,
    ClearChargingProfileStatusType, 
    ChargingLimitSourceType,
    SetMonitoringStatusType
)

logging.getLogger("ocpp").setLevel(logging.DEBUG)
# logging.getLogger("asyncio").setLevel(logging.DEBUG)
# logging.getLogger("websockets").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)

import sys

class ChargePoint(cp):
    def __init__(self, id, connection):
        """Init extra variables for testing."""
        super().__init__(id, connection)
        self.request_id : int = 0
        self.accept: bool = True
        self.reboot: bool = False
        self.display_message: str = ""
        self.messages: list = []
        self.getMessages: list = []
        self.url_firmware: str = ""
    
    @on(Action.SetChargingProfile)
    def on_set_charging_profile(self, **kwargs):
        """Handle set charging profile request."""
        if self.accept is True:
            return call_result.SetChargingProfilePayload(ChargingProfileStatus.accepted)
        else:
            return call_result.SetChargingProfilePayload(ChargingProfileStatus.rejected)
    async def send_heartbeat(self, interval):
        request = call.HeartbeatPayload()
        while True:
            await self.call(request)
            await asyncio.sleep(interval)
    @on(Action.ClearChargingProfile)
    def on_clear_charging_profile(self, **kwargs):
        """Handle clear charging profile request."""
        if self.accept is True:
            return call_result.ClearChargingProfilePayload(
                ClearChargingProfileStatusType.accepted
            )
        else:
            return call_result.ClearChargingProfilePayload(
                ClearChargingProfileStatusType.unknown
            )

    async def send_boot_notification(self):
       request = call.BootNotificationPayload(
               charging_station={
                   'model': 'Wallbox XYZ',
                   'vendor_name': 'anewone'
               },
               reason="PowerUp"
       )
       response = await self.call(request)

       if response.status == 'Accepted':
           print("Connected to central system.") 
        #    await self.send_meter_periodic_data()

           await self.send_heartbeat(response.interval)

    @on(Action.UpdateFirmware)
    async def on_update_firmware(self, firmware: dict(), **kwargs):
        if(self.accept):
            self.url_firmware = firmware["location"]
            return call_result.UpdateFirmwarePayload(status=UpdateFirmwareStatusType.accepted)
        else:
            return call_result.UpdateFirmwarePayload(status=UpdateFirmwareStatusType.rejected)    

    async def send_report_charging_profile(self, **kwargs):
        request = call.ReportChargingProfilesPayload(
            request_id=self.request_id, 
            charging_limit_source=ChargingLimitSourceType.cso, 
            charging_profile=[{
                    "id":222,
                    "stackLevel": 0,
                    "chargingProfileKind": "Absolute",
                    "chargingProfilePurpose": "TxDefaultProfile",
                    "chargingSchedule": [
                        {
                        "id":2222,
                        "chargingRateUnit": "W",
                        "chargingSchedulePeriod": 
                            [{
                                "limit": 30,
                                "startPeriod": 0, 
                            }],
                        
                        }
                    ],
                }], 
            evse_id = 0
        )
        await self.call(request)
        

   # @after(Action.BootNotification)
    async def send_meter_periodic_data(self):
        request = call.MeterValuesPayload(
            evse_id=1,
            
            meter_value=[
                {
                    "timestamp": str(datetime.now()),
                    "sampledValue": [
                        {
                            "value": 1305590.000,
                            "context": "Sample.Periodic",
                            "measurand": "Energy.Active.Import.Register",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.wh, "multiplier":0}
                        },
                        {
                            "value": 50.010,
                            "context": "Sample.Periodic",
                            "measurand": "Frequency",
                            "location": "Outlet",
                        },

                        {
                            "value": 0.000,
                            "context": "Sample.Periodic",
                            "measurand": "Power.Active.Import",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.w, "multiplier":0},
                            "phase": "L1",
                        },
                        {
                            "value": 0.000,
                            "context": "Sample.Periodic",
                            "measurand": "Power.Active.Import",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.w, "multiplier":0},
                            "phase": "L2",
                        },
                        {
                            "value": 0.000,
                            "context": "Sample.Periodic",
                            "measurand": "Power.Active.Import",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.w, "multiplier":0},
                            "phase": "L3",
                        },
                        {
                            "value": 0.000,
                            "context": "Sample.Periodic",
                            "measurand": "Power.Factor",
                            "location": "Outlet",
                        },
                        {
                            "value": 228.000,
                            "context": "Sample.Periodic",
                            "measurand": "Voltage",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.v, "multiplier":0},
                            "phase": "L1-N",
                        },
                        {
                            "value": 228.000,
                            "context": "Sample.Periodic",
                            "measurand": "Voltage",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.v, "multiplier":0},
                            "phase": "L2-N",
                        },
                        {
                            "value": 0.000,
                            "context": "Sample.Periodic",
                            "measurand": "Voltage",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.v, "multiplier":0},
                            "phase": "L3-N",
                        },
                        {
                            "value": 395.900,
                            "context": "Sample.Periodic",
                            "measurand": "Voltage",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.v, "multiplier":0},
                            "phase": "L1-L2",
                        },
                        {
                            "value": 396.300,
                            "context": "Sample.Periodic",
                            "measurand": "Voltage",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.v, "multiplier":0},
                            "phase": "L2-L3",
                        },
                        {
                            "value": 398.900,
                            "context": "Sample.Periodic",
                            "measurand": "Voltage",
                            "location": "Outlet",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.v, "multiplier":0},
                            "phase": "L3-L1",
                        },
                        {
                            "value": 89.00,
                            "context": "Sample.Periodic",
                            "measurand": "Power.Reactive.Import",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.w, "multiplier":0},
                        },
                        {
                            "value": 0.010,
                            "context": "Transaction.Begin",
                            "unitOfMeasure": {"unit": UnitOfMeasureType.kwh, "multiplier":0},
                        },
                        {
                            "value": 1305570.000,
                        },
                    ],
                }
            ],
        )
        while True:
            await self.call(request)
            await asyncio.sleep(10)
        
    @after(Action.UpdateFirmware)
    async def send_firmware_status(self, **kwargs):
        """Send a firmware status notification."""
        request = call.FirmwareStatusNotificationPayload(status=FirmwareStatusType.downloading)
        resp = await self.call(request)
        assert resp is not None

        f = open(self.url_firmware, "r")
        print(f.read())
    
    @on(Action.SetDisplayMessage)
    async def on_set_display_message(self, message : dict, **kwargs):
        response = call_result.SetDisplayMessagePayload(status=DisplayMessageStatusType.accepted)
        self.messages.append(message)

        if(message['priority'] == "AlwaysFront"):
            self.display_message = message['message']['content']
            print(self.display_message)    
        if response.status == "Accepted":
            print(message)
            return response
        else:
            print("Failed to set message")

    @on(Action.ClearDisplayMessage)
    async def on_clear_display_message(self, id: int, **kwargs):
        response = call_result.ClearDisplayMessagePayload(status=DisplayMessageStatusType.accepted)
       
        if response.status == "Accepted":
            count = 0
            for i in self.messages:
                if(i['id'] == id):
                    print(self.messages)
                    del self.messages[count]
                    print(self.messages)
                count+=1
            return response
        else:
            print("Failed to clear message")

    @on(Action.GetDisplayMessages)
    async def on_get_display_message(self, id: list, **kwargs):
        self.getMessages = [item for item in self.messages if item['id'] in id]
        response = call_result.GetDisplayMessagesPayload(status=DisplayMessageStatusType.accepted)
        print(self.getMessages)
        if response.status == "Accepted":
            return response
        else:
            print("Failed to get message")

    @after(Action.GetDisplayMessages)
    async def send_notify_displaymessages_request(self, **kwargs):
        try:
            request = call.NotifyDisplayMessagesPayload(self.request_id, message_info=self.getMessages)
            resp = await self.call(request)
            self.request_id +=1
            return True
        except:
            return False
    
    @on(Action.GetMonitoringReport)
    async def get_monitoring(self, **kwargs):
        print("here")
        return call_result.GetMonitoringReportPayload(status=SetMonitoringStatusType.accepted)

    async def send_security_event(self, **kwargs):
        request = call.SecurityEventNotificationPayload(type="Critical", timestamp=datetime.now(), tech_info="Unauthorized login")
        await self.call(request)
    async def notify_monitoring(self, **kwargs):
        request = call.NotifyMonitoringReportPayload(
            request_id=0, 
            seq_no = 1, 
            generated_at=str(datetime.now()), 
            tbc = False, 
            monitor=[
                {
                    "component":{
                        "name": "Component1"
                    },
                    "variable":{
                        "name": "Variable1"
                    },
                    "variableMonitoring":[{
                        "id": 0,
                        "transaction": False,
                        "value":0,
                        "type":"Periodic",
                        "severity": 3
                    }]
                }

            ])
        await self.call(request)
      

async def main():
    async with websockets.connect('ws://localhost:9000/CP_'+sys.argv[1], subprotocols=['ocpp1.6']) as ws:
        cp = ChargePoint('CP_' + sys.argv[1], ws)
        await asyncio.gather(cp.start(), cp.send_boot_notification(), cp.notify_monitoring())

if __name__ == '__main__':
   asyncio.run(main())