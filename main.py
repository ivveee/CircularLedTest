"""Entry point to the Led Node Testing system


Sets up system configuration in set_up_ventilator
Sets up LED simulation
Runs tests on simulation
"""

import asyncio
import asyncio_dgram
from LEDNode import LEDNode
from LEDOutput import App
from Splitter import Splitter
from SplitterLedSimulator import SplitterLedSimulator
from SplitterVentilator import SplitterVentilator

num_of_splitters = 3


def set_up_ventilator():
    """Ventilator has many (3) splitters
    Splitter has many (4) LED Nodes
    Led Node has many (104) LEDS
    """
    ventilator = SplitterVentilator()
    for splitter_id in range(0, num_of_splitters):
        splitter = Splitter(first_port=0)
        ventilator.add_splitter(splitter, splitter_id)

        node0 = LEDNode(panel_id=0, mode=2)
        node0.set_all_pixels_primary(255, 0, 0, int(255 / (splitter_id + 1)))
        splitter.add_node(node0)

        node1 = LEDNode(panel_id=1, mode=2)
        node1.set_all_pixels_primary(0, 0, 255, int(255 / (splitter_id + 1)))
        splitter.add_node(node1)

        node2 = LEDNode(panel_id=2, mode=2)
        node2.set_all_pixels_primary(0, 255, 0, int(255 / (splitter_id + 1)))
        splitter.add_node(node2)

        node3 = LEDNode(panel_id=3, mode=2)
        node3.set_all_pixels_primary(0, 255, 255, int(255 / (splitter_id + 1)))
        splitter.add_node(node3)

    return ventilator


async def set_color(ventilator: SplitterVentilator, r, g, b, w):
    for sps in ventilator.sps.values():
        for data in sps.splitter.port_data_map:
            data.set_all_pixels_primary(r, g, b, w)
            data.set_all_pixels_secondary(r, g, b, w)


async def entry_point():
    ventilator = set_up_ventilator()
    await ventilator.start()

    simulators = []
    loops = []
    gui = App()
    for i in range(0, num_of_splitters):
        simulator = SplitterLedSimulator(ventilator.sps[i], gui)
        simulators.append(simulator)
        await simulator.start()
        loops.append(simulator.receive_loop())

    bserver = await asyncio_dgram.bind(("127.0.0.255", 16661))

    async def action_code():
        while True:
            data, remote_addr = await bserver.recv()
            print('Package 04')
            for sim in simulators:
                await sim.update()

    async def switch_color():
        """ Test scenarios
        R G B W B transition
        """
        dt = 1
        while True:
            await asyncio.sleep(dt)
            await set_color(ventilator, 255, 0, 0, 255)
            await asyncio.sleep(dt)
            await set_color(ventilator, 0, 255, 0, 255)
            await asyncio.sleep(dt)
            await set_color(ventilator, 0, 0, 255, 255)
            await asyncio.sleep(dt)
            await set_color(ventilator, 0, 0, 0, 255)
            await asyncio.sleep(dt)
            await set_color(ventilator, 255, 255, 255, 255)
            await asyncio.sleep(dt)
            for sps in ventilator.sps.values():
                for i in range(0, 255):
                    sps.splitter.port_data_map[0].set_all_pixels_primary(i, 255, 255, 255)
                    await asyncio.sleep(0.01)
                for i in range(0, 255):
                    sps.splitter.port_data_map[0].set_all_pixels_primary(255, i, 255, 255)
                    await asyncio.sleep(0.01)
                for i in range(0, 255):
                    sps.splitter.port_data_map[0].set_all_pixels_primary(255, 255, i, 255)
                    await asyncio.sleep(0.01)
                for i in range(0, 255):
                    sps.splitter.port_data_map[0].set_all_pixels_primary(255, 255, 255, i)
                    await asyncio.sleep(0.01)

    await asyncio.gather(gui.exec(), ventilator.run_in_loop(), action_code(), *loops, switch_color())

if __name__ == "__main__":
    asyncio.run(entry_point())
