import math
import random

import pytest

from ember.animation import AnimationState, CharacterAnimation, Spring


def test_spring_applies_damped_spring_equation() -> None:
    spring = Spring(value=0, velocity=0, stiffness=100, damping=0.5, target=1)
    dt = 0.01
    damping_coefficient = 2 * math.sqrt(100) * 0.5
    expected_velocity = (100 * (1 - 0) - damping_coefficient * 0) * dt
    expected_value = 0 + expected_velocity * dt

    spring.step(dt)

    assert spring.velocity == pytest.approx(expected_velocity)
    assert spring.value == pytest.approx(expected_value)


def test_spring_caps_delta_time_at_fifty_milliseconds() -> None:
    slow_frame = Spring(target=1)
    capped_frame = Spring(target=1)

    slow_frame.step(0.5)
    capped_frame.step(0.05)

    assert slow_frame.value == pytest.approx(capped_frame.value)
    assert slow_frame.velocity == pytest.approx(capped_frame.velocity)


def test_spring_rejects_negative_delta_time() -> None:
    with pytest.raises(ValueError, match="dt"):
        Spring().step(-0.01)


def test_spring_converges_without_overshooting_for_gaze_settings() -> None:
    spring = Spring(stiffness=260, damping=0.82, target=1)

    for _ in range(300):
        spring.step(1 / 30)

    assert spring.value == pytest.approx(1, abs=0.01)
    assert abs(spring.velocity) < 0.01


def test_all_required_states_are_available() -> None:
    expected = {
        "idle",
        "walking",
        "jumping",
        "falling",
        "listening",
        "thinking",
        "talking",
        "typing",
        "pointing",
        "happy",
        "landing",
        "clinging",
        "perching",
        "yawning",
        "sitting",
        "sleeping",
        "hanging",
        "surprised",
        "confused",
    }

    assert {state.value for state in AnimationState} == expected


def test_typing_state_animates_arms() -> None:
    animation = CharacterAnimation(random.Random(9))
    animation.set_state(AnimationState.TYPING)

    first = animation.update(0.02)
    second = animation.update(0.08)

    assert first.arm_left != second.arm_left
    assert first.arm_right != second.arm_right


def test_listening_gaze_tracks_mouse_within_limits() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.set_state(AnimationState.LISTENING)
    animation.set_mouse_position(400, 0)

    pose = animation.update(0.05)

    assert pose.gaze_x > 0
    assert pose.gaze_y < 0
    assert abs(pose.gaze_x) <= 1
    assert abs(pose.gaze_y) <= 1


def test_sitting_gaze_tracks_pointer_while_looking_toward_chat() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.set_state(AnimationState.SITTING)
    animation.set_mouse_position(280, 190)

    for _ in range(24):
        pose = animation.update(0.05)

    assert pose.gaze_x > 0.5
    assert pose.gaze_y > 0.39

    animation.set_mouse_position(100, 190)
    for _ in range(24):
        pose = animation.update(0.05)

    assert pose.gaze_x < -0.5
    assert pose.gaze_y > 0.39


def test_sleeping_closes_eyes_and_lowers_character() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.set_state(AnimationState.SLEEPING)

    for _ in range(100):
        pose = animation.update(0.05)

    assert pose.closed_eyes
    assert pose.show_sleep_z
    assert pose.sleep_amount > 0.99
    assert 100 + pose.body_y + 86 - 22 * pose.sleep_amount == pytest.approx(
        214, abs=1
    )


def test_blink_timing_can_be_driven_deterministically() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation._blink_wait = 0

    pose = animation.update(0.05)

    assert pose.closed_eyes


def test_landing_puff_fades_to_zero() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.trigger_landing()

    assert animation.update(0.05).landing_amount > 0
    for _ in range(10):
        pose = animation.update(0.05)

    assert pose.landing_amount == 0
    assert animation.state is AnimationState.IDLE


def test_petting_shows_bounded_affection_and_returns_to_idle() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.trigger_affection()
    animation.celebrate()

    pose = animation.update(0.05)

    assert pose.affection_amount > 0
    assert animation.state is AnimationState.HAPPY
    for _ in range(30):
        pose = animation.update(0.05)

    assert pose.affection_amount == 0
    assert animation.state is AnimationState.IDLE


def test_clinging_raises_arms_and_landing_squashes_the_body() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.set_state(AnimationState.CLINGING)
    cling_pose = animation.pose()
    assert cling_pose.arm_left < -60
    assert cling_pose.arm_right > 60

    animation.trigger_landing()
    landing_pose = animation.update(0.05)
    assert animation.state is AnimationState.LANDING
    assert landing_pose.landing_amount > 0
    assert landing_pose.body_stretch < 0


def test_perching_keeps_eyes_open_and_moves_legs_gently() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.set_state(AnimationState.PERCHING)
    first = animation.update(0.05)
    second = animation.update(0.15)

    assert first.eye_opening == 1.0
    assert not first.closed_eyes
    assert first.leg_angles != second.leg_angles
    assert abs(first.body_bob) < 1.0


def test_voice_loudness_is_clamped() -> None:
    animation = CharacterAnimation(random.Random(2))
    animation.set_voice_loudness(3)
    animation.set_state(AnimationState.TALKING)

    assert animation.pose().talking_bounce == 1
