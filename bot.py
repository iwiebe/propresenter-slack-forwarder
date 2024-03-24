import asyncio
import asyncio.mixins
import collections
import logging
from logging.handlers import RotatingFileHandler
import re
import os
import time
import tomllib

import aiohttp
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

import config_example

logger = logging.getLogger("bot")
logger.setLevel(10)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logging.getLogger("root").setLevel(logging.INFO)

home = os.environ["HOME"]
os.makedirs(home + "/Documents/Village Kids Pager", exist_ok=True)

handler = RotatingFileHandler(home + "/Documents/Village Kids Pager/app-log.log", backupCount=3, maxBytes=100000)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


class SetUnsetEvent(asyncio.Event):
    def __init__(self):
        self._waiters = collections.deque()
        self._unset_waiters = collections.deque()
        self._value = False

    def clear(self):
        if self._value:
            self._value = False

            for fut in self._unset_waiters:
                if not fut.done():
                    fut.set_result(True)

    async def wait_unset(self):
        if not self._value:
            return True

        fut = self._get_loop().create_future()  # type: ignore
        self._unset_waiters.append(fut)
        try:
            await fut
            return True
        finally:
            self._unset_waiters.remove(fut)


class DoubleEvent(asyncio.Event):
    def __init__(self):
        self._waiters = collections.deque()
        self._secondary_waiters = collections.deque()
        self._value = False
        self._secondary_value = False

    async def wait_secondary(self):
        if self._secondary_value:
            return True

        fut = self._get_loop().create_future()  # type: ignore
        self._secondary_waiters.append(fut)
        try:
            await fut
            return True
        finally:
            self._secondary_waiters.remove(fut)

    def set_secondary(self):
        if not self._secondary_value:
            self._secondary_value = False

            for fut in self._secondary_waiters:
                if not fut.done():
                    fut.set_result(True)


class Client(AsyncApp):
    def __init__(self) -> None:
        cfg = "config.toml"
        if not os.path.exists(cfg):
            cfg = home + "/Documents/Village Kids Pager/config.toml"
        
        if not os.path.exists(cfg) or os.path.isdir(cfg):
            self.setup_config()
            #raise SystemExit(-1) # TODO: raise notification if not configured (pync?)
        
        with open(cfg) as f:
            self.config = tomllib.loads(f.read())
        
        if not self.config["propresenter"]["password"]:
            raise SystemExit(-1) # TODO: raise notification if not configured (pync?)

        self.version: int = self.config["propresenter"]["v"]
        self.prop_ws: aiohttp.ClientWebSocketResponse | None = None
        self.prop_ws_try_again_at = None
        self.prop_authenticated = False

        self._tasks = []
        self.last_number: str | None = None
        self.pending: dict[str, DoubleEvent] = {}
        self._current_nonce: tuple[str, ...] | None = None

        self.current_batch: list[tuple[str, str]] = []
        self.current_batch_expires: int | None = None

        self.current_formatted = None
    
    def setup_config(self):
        file = home + "/Documents/Village Kids Pager/config.toml"
        os.makedirs(os.path.dirname(file), exist_ok=True)

        if os.path.isdir(file):
            os.rmdir(file)

        with open(file, "w") as f:
            f.write(config_example.example)
        
        print(os.path.abspath(file))

    async def task_add_batch_to_queue(self):
        batch_max: int = self.config["propresenter"]["batch-max-count"]
        batch_wait: int = self.config["propresenter"]["batch-wait-time"]

        while True:
            if not self.current_batch_expires:
                await asyncio.sleep(0)
                continue

            await asyncio.sleep(self.current_batch_expires - time.time())

            if len(self.current_batch) > batch_max:
                batch = self.current_batch[0:batch_max]
                self.current_batch = self.current_batch[batch_max:]
                self.current_batch_expires = int(time.time()) + batch_wait
            else:
                batch = self.current_batch
                self.current_batch = []
                self.current_batch_expires = None

            self.number_queue.put_nowait(tuple(batch)) # type: ignore

    def add_to_queue(self, item: tuple[str, str]) -> None:
        now = int(time.time())
        batch_wait: int = self.config["propresenter"]["batch-wait-time"]

        self.current_batch.append(item)

        if not self.current_batch_expires:
            self.current_batch_expires = now + batch_wait

    def process_number_batch(
        self, items: tuple[tuple[str, str], ...]
    ) -> tuple[str, tuple[str, ...]]:  # returns the formatted numbers and the nonces
        nonces = tuple(item[0] for item in items)
        numbers = tuple(item[1] for item in items)

        ln = len(items)

        if ln == 1:
            return items[0][1], nonces

        formatted = ", ".join(numbers[:-1])
        formatted += f" & {numbers[-1]}"

        return formatted, nonces

    async def task_send_numbers(self) -> None:
        while True:
            logger.info("waiting for slide to free")
            await self.available.wait()
            logger.info("slide free!")

            nums = await self.number_queue.get()
            logger.info(f"got number(s): {nums}, sending!")

            formatted, msg_ids = self.process_number_batch(nums)
            self.current_formatted = formatted

            self._current_nonce = msg_ids
            await self.propres_send_number(formatted)

            if self.version == 7:
                await self.pro7_send_waiter(msg_ids)
                self.current_formatted = None

    async def pro7_send_waiter(self, nonces: tuple[str, ...]) -> None:
        # pro7 doesnt send feedback for setting / hiding, so we have to guess based on timing.
        self.available.clear()

        for nonce in nonces:
            event = self.pending[nonce]
            event.set()

        await asyncio.sleep(self.config["propresenter"]["expire-time"])

        for nonce in nonces:
            event = self.pending[nonce]
            event.set_secondary()

        self._current_nonce = None
        self.available.set()

    async def task_prop_ws_pump(self) -> None:
        while self.prop_ws and not self.prop_ws.closed:
            try:
                msg = await self.prop_ws.receive_json()
            except Exception as e:
                if not self.prop_ws.closed:
                    await self.prop_ws.close()
                
                logger.error("Disconnected from propresenter:", exc_info=e)
                
                asyncio.create_task(self.setup_prop_connection())
                return
                
            logger.debug(f"debug ws: {msg}")
            if msg["action"] == "authenticate":
                self.prop_authenticated = bool(msg["authenticated"])

                if not self.prop_authenticated:
                    logger.warning(f"Could not authenticate with ProPresenter: {msg['error']}")
                    raise SystemExit

                else:
                    logger.info("Authenticated with propresenter!")
                    await self.prop_ws.send_json({"action": "messageRequest"})

            elif msg["action"] == "messageHide":  # PRO6 ONLY, MANUAL TIMER FOR PRO7
                self.available.set()
                if self._current_nonce:
                    for nonce in self._current_nonce:
                        event = self.pending[nonce]
                        event.set_secondary()

                self._current_nonce = None
                self.current_formatted = None

            elif msg["action"] == "messageSend":  # PRO6 ONLY, MANUAL TIMER FOR PRO7
                self.available.clear()
                if self._current_nonce:
                    for nonce in self._current_nonce:
                        event = self.pending[nonce]
                        event.set()
                    
                    self._current_nonce = None
                    self.current_formatted = None
            
            elif msg["action"] == "presentationTriggerIndex": # ignore this event
                return

            else:
                logger.debug("Unknown payload: %s", msg)

    async def pro6_send_hello(self) -> None:
        payload = {"action": "authenticate", "protocol": 600, "password": self.config["propresenter"]["password"]}

        if not self.prop_ws:
            return

        await self.prop_ws.send_json(payload)

    async def pro7_send_hello(self) -> None:
        payload = {"action": "authenticate", "protocol": 701, "password": self.config["propresenter"]["password"]}

        if not self.prop_ws:
            return

        await self.prop_ws.send_json(payload)

    async def propres_send_number(self, number: str) -> None:
        payload = {"action": "messageSend", "messageIndex": 0, "messageKeys": ["Message"], "messageValues": [number]}

        if not self.prop_ws:
            return

        await self.prop_ws.send_json(payload)

    async def propres_cancel_number(self) -> None:
        payload = {"action": "messageHide", "index": 0}

        if not self.prop_ws:
            return

        await self.prop_ws.send_json(payload)

    async def setup_asyncio(self):
        logger.handlers[0].setLevel(logging.DEBUG)

        self.available = SetUnsetEvent()
        self.available.set()

        self.number_queue: asyncio.Queue[tuple[tuple[str, str]]] = asyncio.Queue()

        self._tasks.append(asyncio.create_task(self.task_send_numbers()))
        self._tasks.append(asyncio.create_task(self.task_add_batch_to_queue()))

    async def setup_prop_connection(self):
        client = aiohttp.ClientSession()
        host = self.config["propresenter"]["host"]
        port = self.config["propresenter"]["port"]

        backoff = 1

        while True:

            try:
                self.prop_ws = await client.ws_connect(f"ws://{host}:{port}/remote")
            except Exception as e:
                backoff *= 2
                logger.error("An error occurred while connecting to propresenter:", exc_info=e)
                logger.warning(f"failed to connect to propresenter, setting backoff to {backoff} and waiting to try again")

                await asyncio.sleep(backoff)
                continue
            
            backoff = 1
            client.detach()

            self._tasks.append(asyncio.create_task(self.task_prop_ws_pump()))

            if self.version == 6:
                await self.pro6_send_hello()
            elif self.version == 7:
                await self.pro7_send_hello()
            else:
                raise RuntimeError(f"Version must be 6 or 7, not {self.version}")
            
            break

    async def on_message(self, message: dict) -> None:
        logger.debug("received message from slack: %s", message)
        channel_id: str = message["channel"]
        content: str = message["text"]
        msg_ts: str = message["ts"]

        if channel_id != self.config["bot"]["listen-channel"]:
            return
        
        if content.startswith("!"): # ignore messages that start with !
            return

        async def sender(num: str):
            self.pending[msg_ts] = event = DoubleEvent()
            if (
                self.number_queue.qsize() > 0
                or self._current_nonce
                or len(self.current_batch) >= self.config["propresenter"]["batch-max-count"]
            ):
                logger.debug("queue is busy, hourglassing new number")
                asyncio.create_task(
                    self.client.reactions_add(channel=channel_id, name="hourglass", timestamp=msg_ts)
                )  # HOURGLASS (waiting) # create a task to ignore ratelimit effects

            self.add_to_queue((msg_ts, num))

            await event.wait()
            await self.client.reactions_add(channel=channel_id, name="calling", timestamp=msg_ts)  # CALLING

            await event.wait_secondary()
            await self.client.reactions_add(channel=channel_id, name="thumbsup", timestamp=msg_ts)  # THUMBSUP

            del self.pending[msg_ts]

        number = re.search(r"(?:\d){4}", content)

        if number:
            num = number.group(0)
            if num in self.config["bot"].get("ignore-numbers", []):
                await self.client.reactions_add(channel=channel_id, name="x", timestamp=msg_ts) # RED CROSS
                return

            self.last_number = num
            await sender(self.last_number)

        elif "repeat" in content.lower():
            if self.last_number:
                await sender(self.last_number)
            else:
                await self.client.reactions_add(channel=channel_id, name="thumbsdown", timestamp=msg_ts)

            return

        elif "cancel" in content.lower():
            await self.propres_cancel_number()
            await self.client.reactions_add(channel=channel_id, name="thumbsup", timestamp=msg_ts)
            return

    async def fetch_tokens(self) -> None:
        if "network" not in self.config:
            raise RuntimeError("Unable to fetch tokens, network information not given")
        
        target: str = self.config["network"]["target"]
        auth: str = self.config["network"]["simpleauth-pass"]

        if not target.endswith("/"):
            target += "/"

        async with aiohttp.ClientSession() as session:
            async with session.get(target + "fetch", headers={"Authorization": auth}) as resp:
                if resp.status == 401:
                    raise RuntimeError("Unable to fetch tokens, simpleauth invalid")

                elif resp.status == 400:
                    raise RuntimeError("Unable to fetch tokens, authentication has not been performed: " + await resp.text())

                try:
                    data = await resp.json()
                    self.config["bot"]["app-token"] = data["app-token"]
                    self.config["bot"]["bot-token"] = data["bot-token"]
                    logger.info("Successfully fetched tokens")
                except:
                    logger.critical(await resp.text())
                    raise RuntimeError("Unable to fetch tokens, could not use returned payload")

    async def start(self):
        await self.setup_asyncio()

        if not self.config["bot"].get("app-token", None) or not self.config["bot"].get("bot-token", None):
            logger.info("Tokens not found in config file, attempting to fetch from server")
            await self.fetch_tokens()
        
        super().__init__(token=self.config["bot"]["bot-token"]) # cursed
        self.event("message")(self.on_message)

        asyncio.create_task(self.setup_prop_connection())

        self.handler = AsyncSocketModeHandler(self, self.config["bot"]["app-token"])
        await self.handler.start_async()
    
    def run(self):
        asyncio.run(self.start())
