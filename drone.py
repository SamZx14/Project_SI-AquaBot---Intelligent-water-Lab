"""Sequential drone pumping animation, independent of the renderer and solver."""
from dataclasses import dataclass

JUG_CENTERS = (302.0, 568.0)
SUPPLY_X, DRAIN_X, FLIGHT_SPEED = 110.0, 188.0, 300.0


@dataclass
class Stage:
    kind: str
    duration: float
    site: object
    start_x: float
    end_x: float
    start_water: tuple
    end_water: tuple
    start_cargo: float
    end_cargo: float
    start_tube: float
    end_tube: float
    jug: object = None
    start_pose: tuple = (0.0, 0.0, 0.0, 0.0)
    end_pose: tuple = (0.0, 0.0, 0.0, 0.0)


class DroneController:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = SUPPLY_X
        self.water = [0.0, 0.0]
        self.cargo = self.tube = 0.0
        self.held_jug = None
        self.pose = (0.0, 0.0, 0.0, 0.0)
        self.stages = []
        self.index = 0
        self.elapsed = self.total_elapsed = 0.0

    @property
    def finished(self):
        return self.index >= len(self.stages)

    @property
    def stage(self):
        return None if self.finished else self.stages[self.index]

    @property
    def phase(self):
        return "idle" if self.finished else self.stage.kind

    @property
    def progress(self):
        duration = sum(stage.duration for stage in self.stages)
        return 1.0 if self.finished or not duration else self.total_elapsed/duration

    def start(self, goal):
        """Plan from the visible state, including any water currently in the tank."""
        old_jug, old_pose = self.held_jug, self.pose
        old_site = self.stage.site if self.stage else "supply"
        self.stages = []
        self.index = 0
        self.elapsed = self.total_elapsed = 0.0
        planned_x, planned_water = self.x, self.water[:]
        planned_cargo, planned_tube = self.cargo, self.tube

        planned_pose = old_pose

        def add(kind, duration, site, x=None, water=None, cargo=None, tube=None, jug=None, pose=None):
            nonlocal planned_x, planned_water, planned_cargo, planned_tube, planned_pose
            end_x = planned_x if x is None else x
            end_water = planned_water[:] if water is None else water[:]
            end_cargo = planned_cargo if cargo is None else cargo
            end_tube = planned_tube if tube is None else tube
            if duration > 1e-9:
                self.stages.append(Stage(kind, duration, site, planned_x, end_x,
                    tuple(planned_water), tuple(end_water), planned_cargo, end_cargo,
                    planned_tube, end_tube, jug, planned_pose, planned_pose if pose is None else pose))
            planned_x, planned_water = end_x, end_water
            planned_cargo, planned_tube = end_cargo, end_tube
            if pose is not None:
                planned_pose = pose

        def fly(site):
            x = JUG_CENTERS[site] if isinstance(site, int) else (SUPPLY_X if site == "supply" else DRAIN_X)
            add("fly", abs(x-planned_x)/FLIGHT_SPEED, site, x=x, tube=0)

        def pour(site, amount):
            fly(site)
            water = planned_water[:]
            if isinstance(site, int):
                water[site] += amount
            add("pour" if isinstance(site, int) else "drain", 0.85, site,
                water=water, cargo=max(0, planned_cargo-amount), tube=0)

        # Finish with the tube and leftover tank water before starting a new step.
        if planned_tube > 0:
            add("retract", 0.3*planned_tube, old_site, tube=0)
        if planned_cargo > 1e-8:
            pour("drain", planned_cargo)
        if old_jug is not None and any(abs(v) > 1e-8 for v in old_pose):
            add("upright", 0.3, old_jug, jug=old_jug, pose=(old_pose[0], old_pose[1], 0, 1))
            add("return", max(0.4, abs(planned_x-JUG_CENTERS[old_jug])/FLIGHT_SPEED), old_jug,
                x=JUG_CENTERS[old_jug], jug=old_jug, pose=(0, -110, 0, 1))
            add("land", 0.4, old_jug, jug=old_jug, pose=(0, 0, 0, 1))
            add("release", 0.3, old_jug, jug=old_jug, pose=(0, 0, 0, 0))
        needed = [max(0, goal[i]-planned_water[i]) for i in range(2)]
        for source in range(2):
            amount = max(0, planned_water[source]-goal[source])
            if amount <= 1e-8:
                continue
            fly(source)
            add("grip", 0.35, source, jug=source, pose=(0, 0, 0, 1))
            add("lift", 0.4, source, jug=source, pose=(0, -110, 0, 1))
            destinations = []
            for dest in range(2):
                transfer = min(needed[dest], amount)
                if transfer > 1e-8:
                    destinations.append((dest, transfer))
                    needed[dest] -= transfer
                    amount -= transfer
            if amount > 1e-8:
                destinations.append(("drain", amount))
            for dest, transfer in destinations:
                target_x = JUG_CENTERS[dest] if isinstance(dest, int) else DRAIN_X
                direction = 1 if target_x > JUG_CENTERS[source] else -1
                carry_x = target_x-direction*60
                offset = carry_x-JUG_CENTERS[source]
                add("carry", max(0.4, abs(carry_x-planned_x)/FLIGHT_SPEED), dest,
                    x=carry_x, jug=source, pose=(offset, -110, 0, 1))
                angle = -direction*70
                add("tilt", 0.4, dest, jug=source, pose=(offset, -110, angle, 1))
                water = planned_water[:]
                water[source] -= transfer
                if isinstance(dest, int):
                    water[dest] += transfer
                add("transfer" if isinstance(dest, int) else "empty", 1.15, dest,
                    water=water, jug=source, pose=(offset, -110, angle, 1))
                add("upright", 0.4, dest, jug=source, pose=(offset, -110, 0, 1))
            add("return", max(0.4, abs(planned_x-JUG_CENTERS[source])/FLIGHT_SPEED), source,
                x=JUG_CENTERS[source], jug=source, pose=(0, -110, 0, 1))
            add("land", 0.4, source, jug=source, pose=(0, 0, 0, 1))
            add("release", 0.3, source, jug=source, pose=(0, 0, 0, 0))
        for dest in range(2):
            amount = needed[dest]
            if amount <= 1e-8:
                continue
            fly("supply")
            add("lower", 0.3, "supply", tube=1)
            add("refill", 0.65, "supply", cargo=amount)
            add("retract", 0.25, "supply", tube=0)
            pour(dest, amount)
        # Snap to the exact goal to avoid floating-point leftovers.
        if self.stages:
            self.stages[-1].end_water = tuple(float(v) for v in goal)

    def advance(self, dt):
        """Return unused time after completing the operation."""
        remaining = max(0, dt)
        while remaining > 1e-9 and not self.finished:
            stage = self.stage
            used = min(remaining, stage.duration-self.elapsed)
            self.elapsed += used
            self.total_elapsed += used
            remaining -= used
            t = min(1.0, self.elapsed/stage.duration)
            smooth = t*t*(3-2*t)
            self.held_jug = stage.jug
            self.pose = tuple(a+(b-a)*smooth for a, b in zip(stage.start_pose, stage.end_pose))
            self.x = stage.start_x+(stage.end_x-stage.start_x)*smooth
            self.water = [a+(b-a)*smooth for a, b in zip(stage.start_water, stage.end_water)]
            self.cargo = stage.start_cargo+(stage.end_cargo-stage.start_cargo)*smooth
            self.tube = stage.start_tube+(stage.end_tube-stage.start_tube)*smooth
            if t >= 1:
                self.index += 1
                self.elapsed = 0.0
        if self.finished:
            self.held_jug = None
            self.pose = (0, 0, 0, 0)
        return remaining

    @property
    def description(self):
        if self.finished:
            return ""
        site = self.stage.site
        place = f"jug {'AB'[site]}" if isinstance(site, int) else ("water supply" if site == "supply" else "drain")
        verbs = {"fly": "Flying to", "lower": "Lowering tube into",
                 "retract": "Retracting tube from", "pour": "Pouring water into",
                 "refill": "Taking water from", "drain": "Releasing water into",
                 "grip": "Gripping", "lift": "Lifting", "carry": "Carrying jug to",
                 "tilt": "Tilting jug toward", "transfer": "Pouring directly into",
                 "empty": "Emptying jug into", "upright": "Steadying jug at",
                 "return": "Returning", "land": "Placing", "release": "Releasing"}
        return f"{verbs[self.phase]} {place}"
