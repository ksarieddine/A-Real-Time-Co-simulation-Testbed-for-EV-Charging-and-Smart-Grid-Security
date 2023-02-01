import asyncio
from asyncio.base_subprocess import WriteSubprocessPipeProto
from dataclasses import dataclass
import logging
from sqlite3 import connect
import websockets
from datetime import datetime, timedelta, timezone
import time
from ocpp.routing import on, after
from ocpp.v201 import ChargePoint as cp, call, call_result
from ocpp.messages import CallError
from ocpp.exceptions import NotImplementedError
from ocpp.v201.enums import (
    Action,
    FirmwareStatusType,
    UpdateFirmwareStatusType,
    DisplayMessageStatusType,
    PublishFirmwareStatusType,
    UnpublishFirmwareStatusType,
    InstallCertificateUseType,
    ChargingProfilePurposeType,
    ChargingProfileKindType,
    ChargingProfilePurposeType,
    ChargingProfileStatus,
    ChargingRateUnitType,
    ClearChargingProfileStatusType
)


_LOGGER: logging.Logger = logging.getLogger(__package__)
logging.getLogger("ocpp").setLevel(logging.DEBUG)
# Uncomment these when Debugging
# logging.getLogger("asyncio").setLevel(logging.DEBUG)
# logging.getLogger("websockets").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)


cp_id = []
charge_points = {}

class ChargePoint(cp):
    def __init__(self, id, connection):
        super().__init__(id, connection)
        self.status: str = "OK"
        self.request_id: int = 0
        self.firmware_status: str = "Idle"
        self.request_id = 0
    
    async def post_connect(self, **kwargs):
        self.status = "OK"

    @on(Action.BootNotification)
    #v1.6
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status='Accepted'
        )
    @on(Action.Heartbeat)
    async def on_heartbeat(self):
        print('Got a Heartbeat!')
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') + "Z"
        )

    #@after(Action.BootNotification)
    async def set_display_message(self, **kwargs):
        n_message = input("Set a message:")
        request = call.SetDisplayMessagePayload(message= {
            "id": self.request_id, 
            "priority": "AlwaysFront",
            "state" : "Idle",
            "message":{
                "format": "UTF8", 
                "content":n_message
                }
            })
        resp = await self.call(request)
        self.request_id += 1
        if resp.status == DisplayMessageStatusType.accepted:
            print("Message Sent Successfully")
            return True
        else:
            return False

    async def send_clear_displaymessage_request(self, **kwargs):
        id = int(input("Enter message ID"))
        request = call.ClearDisplayMessagePayload(id = id)
        resp = await self.call(request)
        if resp.status == DisplayMessageStatusType.accepted:
            print("Message Sent Successfully")
            return True
        else:
            return False 
    @after(Action.BootNotification)
    async def send_get_monitoring_report(self, **kwargs):
        request = call.GetMonitoringReportPayload(request_id = 0)
        await self.call(request)
        
        
    async def get_display_message(self, **kwargs):
        id = int(input("Enter message ID"))
        request = call.GetDisplayMessagesPayload(request_id = self.request_id, id = [id])
        resp = await self.call(request)  
        self.request_id += 1

        if resp.status == DisplayMessageStatusType.accepted:
            print("Message Sent Successfully")
            return True
        else:
            return False

    async def set_charging_profile(self, **kwargs):
        request = call.SetChargingProfilePayload(
            evse_id=0,
                charging_profile={
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
                },
            )        
        resp = await self.call(request)  
        self.request_id += 1

    @on(Action.ReportChargingProfiles)
    def on_report_charging_profile(self, **kwargs):
        return call_result.ReportChargingProfilesPayload()

    @on(Action.MeterValues)
    def on_meter_values(self, evse_id: int, meter_value: dict, **kwargs):
        return call_result.MeterValuesPayload()
    
    async def clear_profile(self):
        """Clear all charging profiles."""
        req = call.ClearChargingProfilePayload()
        resp = await self.call(req)
        if resp.status == ClearChargingProfileStatusType.accepted:
            return True
        else:
            _LOGGER.warning("Failed with response: %s", resp.status)
            await self.notify_ha(
                f"Warning: Clear profile failed with response {resp.status}"
            )
            return False
    
            
    async def send_update_firmware_request(self, firmware_url: str, retry_interval: int = 0, retries : int = 1, **kwargs):
        self.request_id = self.request_id + 1
        request = call.UpdateFirmwarePayload(request_id=self.request_id, firmware={"location": firmware_url, "retrieveDateTime":"23062022-20:40"}, retry_interval=retry_interval, retries=retries)
        resp = await self.call(request)
        if resp.status == UpdateFirmwareStatusType.accepted:
            return True
        else:
            print("Failed")
            return False
    @on(Action.NotifyMonitoringReport)
    async def notify_monitoring(self, **kwargs):
        return call_result.NotifyMonitoringReportPayload()
    
    @on(Action.NotifyDisplayMessages)
    async def on_notify_displaymessages_request(self, **kwargs):
        return call_result.NotifyDisplayMessagesPayload()

    @on(Action.FirmwareStatusNotification)
    def on_firmware_status(self, status, **kwargs):
        """Handle firmware status notification."""
        self.firmware_status = status
        return call_result.FirmwareStatusNotificationPayload()
    
    async def start(self):
        """Start charge point."""
        await self.run([super().start(), self.post_connect()])
        
    async def run(self, tasks):
        """Run a specified list of tasks."""
        self.tasks = [asyncio.ensure_future(task) for task in tasks]
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.TimeoutError:
            pass
        except websockets.exceptions.WebSocketException as websocket_exception:
            _LOGGER.debug(f"Connection closed to '{self.id}': {websocket_exception}")
        except Exception as other_exception:
            _LOGGER.error(
                f"Unexpected exception in connection to '{self.id}': '{other_exception}'",
                exc_info=True,
            )
        finally:
            await self.stop()

    async def stop(self):
        """Close connection and cancel ongoing tasks."""
        self.status = "Unavailable"
        if self._connection.open:
            _LOGGER.debug(f"Closing websocket to '{self.id}'")
            await self._connection.close()
        for task in self.tasks:
            task.cancel()
        
    async def reconnect(self, connection):
        _LOGGER.debug(f"Reconnect websocket to {self.id}")
        await self.stop()
        self.status = "OK"
        self._connection = connection
        if self.status == "OK":
            await self.run([super().start()])
        else:
            await self.run([super().start(), self.post_connect()])
    @on(Action.SecurityEventNotification)
    async def on_security_event(self, **kwargs):
        return call_result.SecurityEventNotificationPayload()

async def on_connect(websocket, path):
    """ For every new charge point that connects, create a ChargePoint
    instance and start listening for messages.
    """
    try:
        requested_protocols = websocket.request_headers[
            'Sec-WebSocket-Protocol']
    except KeyError:
        logging.info("Client hasn't requested any Subprotocol. "
                 "Closing Connection")
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning('Protocols Mismatched | Expected Subprotocols: %s,'
                        ' but client supports  %s | Closing connection',
                        websocket.available_subprotocols,
                        requested_protocols)
        return await websocket.close()

    _LOGGER.info(f"Charger websocket path={path}")
    charge_point_id = path.strip('/')
    
    if charge_point_id not in cp_id:
        _LOGGER.info(f"Charger {charge_point_id} connected is connected.")
        cp = ChargePoint(charge_point_id, websocket)
        charge_points[charge_point_id] = cp
        cp_id.append(charge_point_id)
        await cp.start()
    else:
        print("hello")
        _LOGGER.info(f"Charger {charge_point_id} reconnected.")
        cp: ChargePoint = charge_points[charge_point_id]
        await cp.reconnect(websocket)
    _LOGGER.info(f"Charger {cp_id} disconnected.")

async def main():
    server = await websockets.serve(
        on_connect,
        '0.0.0.0',
        9000,
        subprotocols=['ocpp1.6']
    )
    _LOGGER.info(f"WebSocket Server Started")
    await server.wait_closed()
    
    

if __name__ == '__main__':
    asyncio.run(main())