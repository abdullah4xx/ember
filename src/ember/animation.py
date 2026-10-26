"""Time-step-independent animation state for Ember."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import random


class AnimationState(str, Enum):
    IDLE = "idle"
    WALKING = "walking"
    JUMPING = "jumping"
    FALLING = "falling"
    LISTENING = "listening"
    THINKING = "thinking"
    TALKING = "talking"
    TYPING = "typing"
    POINTING = "pointing"
    HAPPY = "happy"
    LANDING = "landing"
    CLINGING = "clinging"
    PERCHING = "perching"
    YAWNING = "yawning"
    SITTING = "sitting"
    SLEEPING = "sleeping"
    HANGING = "hanging"
    SURPRISED = "surprised"
    CONFUSED = "confused"


@dataclass
class Spring:
    value: float = 0.0
    velocity: float = 0.0
    stiffness: float = 260.0
    damping: float = 0.82
    target: float = 0.0

    def step(self, dt: float) -> float:
        if dt < 0:
            raise ValueError("dt must not be negative")
        dt = min(dt, 0.05)
        c = 2 * math.sqrt(self.stiffness) * self.damping
        self.velocity += (
            self.stiffness * (self.target - self.value) - c * self.velocity
        ) * dt
        self.value += self.velocity * dt
        return self.value


@dataclass(frozen=True)
class Pose:
    effect_phase: float
    body_y: float
    body_bob: float
    body_stretch: float
    lean: float
    arm_left: float
    arm_right: float
    leg_angles: tuple[float, float, float, float]
    gaze_x: float
    gaze_y: float
    closed_eyes: bool
    eye_opening: float
    happy_eyes: bool
    thought_dots: int
    talking_bounce: float
    sleep_amount: float
    landing_amount: float
    point_on_left: bool
    show_sleep_z: bool
    surprised: bool
    affection_amount: float
    mouth_opening: float


class CharacterAnimation:
    """Animation controller; callers provide elapsed seconds and input state."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.state = AnimationState.IDLE
        self.facing = 1
        self.gaze_x = Spring(stiffness=260, damping=0.82)
        self.gaze_y = Spring(stiffness=260, damping=0.82)
        self.hop = Spring(stiffness=260, damping=0.35)
        self.lean = Spring(stiffness=60, damping=0.8)
        self.sleep = Spring(stiffness=60, damping=0.8)
        self.mouse_position: tuple[float, float] | None = None
        self.point_target: tuple[float, float] | None = None
        self.voice_loudness = 0.0
        self.sleepiness = 0.0
        self.elapsed = 0.0
        self.state_elapsed = 0.0
        self.landing_remaining = 0.0
        self.affection_remaining = 0.0
        self._landing_return_state = AnimationState.IDLE
        self._happy_return_state = AnimationState.IDLE
        self._blink_remaining = 0.0
        self._double_blink_pending = False
        self._blink_wait = self.rng.uniform(2.0, 5.0)

    def set_state(self, state: AnimationState | str) -> None:
        new_state = AnimationState(state)
        if new_state is self.state:
            return
        previous_state = self.state
        self.state = new_state
        self.state_elapsed = 0.0
        if new_state is AnimationState.LANDING:
            self._landing_return_state = previous_state
        elif new_state is AnimationState.HAPPY:
            self._happy_return_state = previous_state
        if new_state is AnimationState.SLEEPING:
            self.sleepiness = 1.0
        elif new_state in (AnimationState.SITTING, AnimationState.YAWNING):
            self.sleepiness = max(self.sleepiness, 0.65)
        else:
            self.sleepiness = 0.0

    def celebrate(
        self, return_state: AnimationState | None = None
    ) -> None:
        previous_state = self.state
        self.set_state(AnimationState.HAPPY)
        self._happy_return_state = return_state or previous_state

    def trigger_affection(self) -> None:
        self.affection_remaining = 1.15

    def set_facing(self, direction: int) -> None:
        if direction not in (-1, 1):
            raise ValueError("direction must be -1 or 1")
        self.facing = direction

    def set_mouse_position(self, x: float, y: float) -> None:
        self.mouse_position = (x, y)

    def set_point_target(self, x: float, y: float) -> None:
        self.point_target = (x, y)

    def set_voice_loudness(self, loudness: float) -> None:
        self.voice_loudness = min(1.0, max(0.0, loudness))

    def set_sleepiness(self, amount: float) -> None:
        self.sleepiness = min(1.0, max(0.0, amount))

    def trigger_landing(self) -> None:
        self.landing_remaining = 0.42
        self.set_state(AnimationState.LANDING)

    def update(self, dt: float) -> Pose:
        if dt < 0:
            raise ValueError("dt must not be negative")
        dt = min(dt, 0.05)
        self.elapsed += dt
        self.state_elapsed += dt
        self.landing_remaining = max(0.0, self.landing_remaining - dt)
        self.affection_remaining = max(0.0, self.affection_remaining - dt)
        if (
            self.state is AnimationState.LANDING
            and self.landing_remaining == 0.0
        ):
            self.set_state(self._landing_return_state)
        elif (
            self.state is AnimationState.HAPPY
            and self.state_elapsed >= 1.25
        ):
            self.set_state(self._happy_return_state)
        self._update_blink(dt)
        self._update_targets()
        self.gaze_x.step(dt)
        self.gaze_y.step(dt)
        self.hop.step(dt)
        self.lean.step(dt)
        self.sleep.step(dt)
        return self.pose()

    def pose(self) -> Pose:
        walk_phase = self.elapsed * 8.0
        walking = self.state is AnimationState.WALKING
        happy = self.state is AnimationState.HAPPY
        sleeping = self.state is AnimationState.SLEEPING
        sitting = self.state is AnimationState.SITTING
        perching = self.state is AnimationState.PERCHING
        talking = self.state is AnimationState.TALKING
        typing = self.state is AnimationState.TYPING
        yawning = self.state is AnimationState.YAWNING
        landing = self.state is AnimationState.LANDING

        leg_angles = tuple(
            math.sin(walk_phase + (math.pi if index % 2 else 0.0)) * 28.0
            if walking
            else (
                math.sin(self.elapsed * 1.9 + index * 0.55) * 4.0
                if perching
                else (
                    math.sin(walk_phase + (math.pi if index % 2 else 0.0))
                    * 7.0
                    * (1.0 - self.sleep.value)
                    if self.state
                    in (
                        AnimationState.JUMPING,
                        AnimationState.FALLING,
                        AnimationState.HAPPY,
                        AnimationState.LANDING,
                    )
                    else 0.0
                )
            )
            for index in range(4)
        )
        body_bob = (
            abs(math.sin(walk_phase * 2.0)) * 2.2 if walking else 0.0
        )
        if not walking and not sleeping and not sitting and not perching:
            body_bob += abs(math.sin(self.elapsed * 2.2)) * 1.1
        if perching:
            body_bob += math.sin(self.elapsed * 1.35) * 0.55
        if talking:
            body_bob += abs(math.sin(self.elapsed * 10.0)) * (
                1.5 + self.voice_loudness * 4.0
            )
        if yawning:
            body_bob += math.sin(min(self.state_elapsed / 1.6, 1.0) * math.pi) * 2.0

        hop_amount = self.hop.value
        if happy:
            hop_amount += max(0.0, math.sin(self.elapsed * 5.2)) * 8.0
        if self.state is AnimationState.JUMPING:
            jump_progress = min(self.state_elapsed / 0.55, 1.0)
            hop_amount += math.sin(jump_progress * math.pi) * 20.0
        body_stretch = self.hop.value * 0.012
        if self.state is AnimationState.FALLING:
            body_stretch += 0.08
        if yawning:
            body_stretch += 0.1 * math.sin(
                min(self.state_elapsed / 1.6, 1.0) * math.pi
            )
        if self.landing_remaining > 0:
            landing_progress = 1.0 - self.landing_remaining / 0.42
            body_stretch -= 0.12 * math.sin(landing_progress * math.pi)

        arm_swing = (
            math.sin(walk_phase) * 12.0
            if walking
            else math.sin(self.elapsed * 1.5) * 1.3
            if perching
            else math.sin(self.elapsed * 2.6) * 2.5
        )
        arm_left = -self.lean.value * 180.0 + arm_swing
        arm_right = self.lean.value * 180.0 - arm_swing
        if talking:
            swing = math.sin(self.elapsed * 10.0) * (9.0 + 12.0 * self.voice_loudness)
            arm_left += swing
            arm_right -= swing
        if typing:
            typing_swing = math.sin(self.elapsed * 24.0) * 7.0
            arm_left = -18.0 + typing_swing
            arm_right = 18.0 - typing_swing
        if self.state is AnimationState.FALLING:
            arm_left = -32.0
            arm_right = 32.0
        if landing:
            arm_left = 38.0
            arm_right = -38.0
        if self.state is AnimationState.CLINGING:
            arm_left = -70.0
            arm_right = 70.0
        if yawning:
            arm_left += 42.0
            arm_right -= 42.0
        if self.state is AnimationState.HANGING:
            arm_left = 45.0
            arm_right = -45.0

        point_on_left = False
        if self.state is AnimationState.POINTING:
            target = self.point_target or (320.0, 90.0)
            pivot_x = 130.0 if target[0] < 190.0 else 250.0
            point_on_left = pivot_x == 130.0
            target_angle = math.degrees(
                math.atan2(target[1] - 141.0, target[0] - pivot_x)
            )
            arm_angle = target_angle - (180.0 if point_on_left else 0.0)
            if point_on_left:
                arm_left = arm_angle
            else:
                arm_right = arm_angle

        sleep_amount = min(1.0, max(0.0, self.sleep.value))
        body_y = 50.0 * sleep_amount - hop_amount + body_bob
        if self.state is AnimationState.FALLING:
            body_y += 3.0
        thought_dots = 0
        if self.state is AnimationState.THINKING:
            thought_dots = 1 + int(self.elapsed * 2.8) % 3

        eye_opening = (
            0.0
            if sleeping
            else min(1.0, self.state_elapsed / 1.1)
            if self.state is AnimationState.HANGING and self.state_elapsed < 1.1
            else 0.0
            if self._blink_remaining > 0
            else 1.0
        )
        eyes_closed = (
            sleeping
            or self._blink_remaining > 0
            or (
                self.state is AnimationState.HANGING
                and eye_opening < 1.0
            )
        )
        return Pose(
            effect_phase=self.elapsed,
            body_y=body_y,
            body_bob=body_bob,
            body_stretch=body_stretch,
            lean=(
                self.lean.value
                + (0.14 * self.facing if self.state is AnimationState.CONFUSED else 0.0)
                + (0.055 * math.sin(self.elapsed * 1.3) if sleeping else 0.0)
            ),
            arm_left=arm_left,
            arm_right=arm_right,
            leg_angles=leg_angles,
            gaze_x=self.gaze_x.value,
            gaze_y=self.gaze_y.value,
            closed_eyes=eyes_closed,
            eye_opening=eye_opening,
            happy_eyes=happy,
            thought_dots=thought_dots,
            talking_bounce=self.voice_loudness if talking else 0.0,
            sleep_amount=sleep_amount,
            landing_amount=min(1.0, self.landing_remaining / 0.42),
            point_on_left=point_on_left,
            show_sleep_z=sleeping,
            surprised=self.state is AnimationState.SURPRISED,
            affection_amount=min(1.0, self.affection_remaining / 1.15),
            mouth_opening=(
                max(0.0, math.sin(self.elapsed * 13.0))
                if talking
                else 0.0
            ),
        )

    def _update_targets(self) -> None:
        self.lean.target = (
            0.12 * self.facing
            if self.state is AnimationState.WALKING
            else 0.0
        )
        self.sleep.target = (
            1.0
            if self.state is AnimationState.SLEEPING
            else 0.55
            if self.state is AnimationState.SITTING
            else 0.0
        )
        if self.state is AnimationState.HAPPY:
            self.hop.target = max(0.0, math.sin(self.elapsed * 5.2)) * 4.0
        elif self.state is AnimationState.JUMPING:
            progress = min(self.state_elapsed / 0.55, 1.0)
            self.hop.target = math.sin(progress * math.pi) * 12.0
        else:
            self.hop.target = 0.0

        gaze_x = gaze_y = 0.0
        if self.state is AnimationState.PERCHING:
            gaze_y = 0.42
        elif self.state is AnimationState.SITTING:
            gaze_y = 0.65
            if self.mouse_position is not None:
                gaze_x = min(
                    0.9,
                    max(-0.9, (self.mouse_position[0] - 190.0) / 90.0),
                )
                gaze_y = max(
                    0.4,
                    min(
                        0.9,
                        (self.mouse_position[1] - 156.0) / 90.0,
                    ),
                )
        elif self.mouse_position and self.state not in (
            AnimationState.SLEEPING,
            AnimationState.THINKING,
            AnimationState.CONFUSED,
            AnimationState.SURPRISED,
        ):
            gaze_x = min(0.9, max(-0.9, (self.mouse_position[0] - 190.0) / 90.0))
            gaze_y = min(0.9, max(-0.9, (self.mouse_position[1] - 156.0) / 70.0))
        elif self.state is AnimationState.THINKING:
            gaze_y = -0.8
        elif self.state is AnimationState.CONFUSED:
            gaze_x = 0.6 * self.facing
            gaze_y = -0.25
        elif self.state is AnimationState.SURPRISED:
            gaze_y = -0.15
        self.gaze_x.target = gaze_x
        self.gaze_y.target = gaze_y

    def _update_blink(self, dt: float) -> None:
        if self.state is AnimationState.SLEEPING:
            self._blink_remaining = 0.0
            return
        self._blink_remaining = max(0.0, self._blink_remaining - dt)
        self._blink_wait -= dt
        if self._blink_wait > 0.0 or self._blink_remaining > 0.0:
            return
        duration = 0.24 if self.sleepiness > 0.5 else 0.12
        if self._double_blink_pending:
            self._double_blink_pending = False
            self._blink_wait = 0.14
        else:
            self._double_blink_pending = self.rng.random() < 0.2
            self._blink_wait = self.rng.uniform(2.0, 5.0)
        self._blink_remaining = duration
