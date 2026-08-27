from .station import Station
from .line import Line
from .world import World
from .world_data_access_interface import WorldDataAccessInterface


class WorldBuilder:

    def instantiate_station(self, record: dict) -> Station:
        """Build a Station from the wait-rules entry <record>."""
        station = Station(
            name=record["name"],
            rule_name=record["rule_name"],
            rule=record["rule"],
            times_visited=record["times_visited"],
            waited_at=record["waited_at"],
            coordinates=record["coordinates"],
            end=record["end"],
        )
        station.set_id(record["id"])
        return station

    def build_world(self, dao: WorldDataAccessInterface) -> World:
        """Build the World for the DAO's currently loaded map, wiring each station's
        roads as one-way lines between the built stations."""
        world = World()
        stations = [self.instantiate_station(record) for record in dao.get_records()]
        world.add_stations(stations)
        by_id = {station.id: station for station in stations}
        for record in dao.get_records():
            for road in record["roads"]:
                world.add_line(
                    Line(
                        _from=by_id[record["id"]],
                        _to=by_id[road["to"]],
                        length=road["length"],
                    )
                )
        return world
