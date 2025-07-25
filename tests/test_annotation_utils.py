# @author lucasmiranda42
# encoding: utf-8
# module deepof

"""

Testing module for deepof.annotation_utils

"""
import os
import pickle
from itertools import combinations
from shutil import rmtree

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra.pandas import columns, data_frames, range_indexes
from shapely.geometry import Point, Polygon

import deepof.annotation_utils
import deepof.data
import deepof.utils


@settings(deadline=None)
@given(
    pos_dframe=data_frames(
        index=range_indexes(min_size=5),
        columns=columns(["X1", "y1", "X2", "y2"], dtype=float),
        rows=st.tuples(
            st.floats(min_value=1, max_value=10, allow_nan=False, allow_infinity=False),
            st.floats(min_value=1, max_value=10, allow_nan=False, allow_infinity=False),
            st.floats(min_value=1, max_value=10, allow_nan=False, allow_infinity=False),
            st.floats(min_value=1, max_value=10, allow_nan=False, allow_infinity=False),
        ),
    ),
    tol=st.floats(min_value=0.01, max_value=4.98),
)
def test_close_single_contact(pos_dframe, tol):

    idx = pd.MultiIndex.from_product(
        [["bpart1", "bpart2"], ["X", "y"]], names=["bodyparts", "coords"]
    )
    pos_dframe.columns = idx
    close_contact = deepof.annotation_utils.close_single_contact(
        pos_dframe, "bpart1", "bpart2", tol,
    )
    assert close_contact.dtype == bool
    assert np.array(close_contact).shape[0] <= pos_dframe.shape[0]


@settings(deadline=None)
@given(
    pos_dframe=data_frames(
        index=range_indexes(min_size=5),
        columns=columns(["X1", "y1", "X2", "y2", "X3", "y3", "X4", "y4"], dtype=float),
        rows=st.tuples(
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
            st.floats(min_value=1, max_value=10),
        ),
    ),
    tol=st.floats(min_value=0.01, max_value=4.98),
    rev=st.booleans(),
)
def test_close_double_contact(pos_dframe, tol, rev):

    idx = pd.MultiIndex.from_product(
        [["bpart1", "bpart2", "bpart3", "bpart4"], ["X", "y"]],
        names=["bodyparts", "coords"],
    )
    pos_dframe.columns = idx
    close_contact = deepof.annotation_utils.close_double_contact(
        pos_dframe, "bpart1", "bpart2", "bpart3", "bpart4", tol, rev
    )
    assert close_contact.dtype == bool
    assert np.array(close_contact).shape[0] <= pos_dframe.shape[0]


@settings(deadline=None)
@given(
    center=st.tuples(
        st.integers(min_value=300, max_value=500),
        st.integers(min_value=300, max_value=500),
    ),
    axes=st.tuples(
        st.integers(min_value=300, max_value=500),
        st.integers(min_value=300, max_value=500),
    ),
    angle=st.floats(min_value=0, max_value=360),
    tol=st.data(),
    mouse_len=st.floats(min_value=10,max_value=60),
)
def test_climb_wall(center, axes, angle, tol, mouse_len):

    arena = (center, axes, np.radians(angle))
    tol1 = tol.draw(st.floats(min_value=0.001, max_value=1))
    tol2 = tol.draw(st.floats(min_value=tol1, max_value=1))

    prun = (
        deepof.data.Project(
            project_path=os.path.join(
                ".", "tests", "test_examples", "test_single_topview"
            ),
            video_path=os.path.join(
                ".", "tests", "test_examples", "test_single_topview", "Videos"
            ),
            table_path=os.path.join(
                ".", "tests", "test_examples", "test_single_topview", "Tables"
            ),
            arena="circular-autodetect",
            video_scale=int(arena[2]),
            video_format=".mp4",
            table_format=".h5",
        )
        .create(force=True, test=True)
        .get_coords()
    )

    climb1 = deepof.annotation_utils.climb_arena(
        "circular-autodetect", arena, prun["test"], tol1, "", mouse_len,
    )
    climb2 = deepof.annotation_utils.climb_arena(
        "circular-autodetect", arena, prun["test"], tol2, "", mouse_len,
    )
    climb3 = deepof.annotation_utils.climb_arena(
        "polygonal-manual",
        [[-1, -1], [-1, 1], [1, 1], [1, -1]],
        prun["test"],
        tol1,
        "",
        mouse_len,
    )

    rmtree(
        os.path.join(
            ".", "tests", "test_examples", "test_single_topview", "deepof_project"
        )
    )
    
    assert climb1.dtype == bool
    assert climb2.dtype == bool
    assert climb3.dtype == bool
    assert np.sum(climb1) >= np.sum(climb2)

    with pytest.raises(NotImplementedError):
        deepof.annotation_utils.climb_arena("", arena, prun["test"], tol1, "", mouse_len)


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(animal_id=st.one_of(st.just("B"), st.just("W")))
def test_single_animal_traits(animal_id):

    prun = deepof.data.Project(
        project_path=os.path.join(".", "tests", "test_examples", "test_multi_topview"),
        video_path=os.path.join(
            ".", "tests", "test_examples", "test_multi_topview", "Videos"
        ),
        table_path=os.path.join(
            ".", "tests", "test_examples", "test_multi_topview", "Tables"
        ),
        arena="circular-autodetect",
        animal_ids=["B", "W"],
        video_scale=380,
        video_format=".mp4",
        table_format=".h5",
        exclude_bodyparts=["Tail_1", "Tail_2", "Tail_tip"],
    ).create(force=True, test=True)

    features = {
        _id: deepof.post_hoc.align_deepof_kinematics_with_unsupervised_labels(
            prun, animal_id=_id, include_angles=False
        )
        for _id in prun._animal_ids
    }[animal_id]["test"]
    pos_dframe = prun.get_coords(
        center="Center", align="Spine_1", selected_id=animal_id
    )["test"]
    speed_dframe = prun.get_coords(speed=1, selected_id=animal_id)["test"]

    # Downloads immobility model if not already loaded
    huddle_clf = deepof.utils.load_precompiled_model(
        None,
        download_path="https://datashare.mpcdf.mpg.de/s/kiLpLy1dYNQrPKb/download",
        model_path=os.path.join("trained_models", "deepof_supervised","deepof_supervised_huddle_estimator.pkl"),
        model_name="Immobility classifier"
    ) 

    huddling, sleeping = deepof.annotation_utils.immobility(
        features, huddle_estimator=huddle_clf, animal_id=animal_id+"_",
    )
    huddling = huddling.astype(int)

    rmtree(
        os.path.join(
            ".", "tests", "test_examples", "test_multi_topview", "deepof_project"
        )
    )

    assert huddling.dtype == int
    assert np.array(huddling).shape[0] == pos_dframe.shape[0]
    assert np.sum(np.array(huddling)) <= pos_dframe.shape[0]


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    distance_dframe=data_frames(
        index=range_indexes(min_size=20, max_size=20),
        columns=columns(
            ["d1", "d2", "d3", "d4"],
            dtype=float,
            elements=st.floats(min_value=-20, max_value=20),
        ),
    ),
    position_dframe=data_frames(
        index=range_indexes(min_size=20, max_size=20),
        columns=columns(
            ["X1", "y1", "X2", "y2", "X3", "y3", "X4", "y4"],
            dtype=float,
            elements=st.floats(min_value=-20, max_value=20),
        ),
    ),
    speeds_dframe=data_frames(
        index=range_indexes(min_size=20, max_size=20),
        columns=columns(
            ["A_Nose", "B_Nose", "A_Tail_base", "B_Tail_base"],
            dtype=float,
            elements=st.floats(min_value=0, max_value=20),
        ),
    ),
    frames=st.integers(min_value=1, max_value=20),
    tol=st.floats(min_value=0.01, max_value=4.98),
)
def test_following_path(distance_dframe, position_dframe, speeds_dframe, frames, tol):

    bparts = ["A_Nose", "B_Nose", "A_Tail_base", "B_Tail_base"]

    pos_idx = pd.MultiIndex.from_product(
        [bparts, ["X", "y"]], names=["bodyparts", "coords"]
    )

    position_dframe.columns = pos_idx
    distance_dframe.columns = [c for c in combinations(bparts, 2) if c[0][0] != c[1][0]]

    follow = deepof.annotation_utils.following_path(
        distance_dframe,
        position_dframe,
        speeds_dframe,
        follower="A",
        followed="B",
        frames=frames,
        tol=tol,
    )

    assert follow.dtype == bool
    assert len(follow) == position_dframe.shape[0]
    assert len(follow) == distance_dframe.shape[0]
    assert np.sum(follow) <= position_dframe.shape[0]
    assert np.sum(follow) <= distance_dframe.shape[0]


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    behaviour_dframe=data_frames(
        index=range_indexes(min_size=100, max_size=1000),
        columns=columns(
            ["d1", "d2", "d3", "d4", "speed1"], dtype=bool, elements=st.booleans()
        ),
    ),
    window_size=st.data(),
    stepped=st.booleans(),
)
def test_max_behaviour(behaviour_dframe, window_size, stepped):
    wsize1 = window_size.draw(st.integers(min_value=5, max_value=50))
    wsize2 = window_size.draw(st.integers(min_value=wsize1, max_value=50))

    maxbe1 = deepof.annotation_utils.max_behaviour(behaviour_dframe, wsize1, stepped)
    maxbe2 = deepof.annotation_utils.max_behaviour(behaviour_dframe, wsize2, stepped)

    assert isinstance(maxbe1, np.ndarray)
    assert isinstance(maxbe2, np.ndarray)
    if not stepped:
        assert isinstance(maxbe1[wsize1 // 2 + 1], str)
        assert isinstance(maxbe1[wsize2 // 2 + 1], str)
        assert maxbe1[wsize1 // 2 + 1] in behaviour_dframe.columns
        assert maxbe2[wsize2 // 2 + 1] in behaviour_dframe.columns
        assert len(maxbe1) >= len(maxbe2)


def test_get_hparameters():
    #create fake coords 
    prun = deepof.data.Project(
    project_path=os.path.join(".", "tests", "test_examples", "test_multi_topview"),
    video_path=os.path.join(
        ".", "tests", "test_examples", "test_multi_topview", "Videos"
    ),
    table_path=os.path.join(
        ".", "tests", "test_examples", "test_multi_topview", "Tables"
    ),
    arena="circular-autodetect",
    animal_ids=["B", "W"],
    video_scale=380,
    video_format=".mp4",
    table_format=".h5",
    exclude_bodyparts=["Tail_1", "Tail_2", "Tail_tip"],
    ).create(force=True, test=True)

    prun.reset_supervised_parameters()
    assert isinstance(prun.get_supervised_parameters(), dict)
    prun.set_supervised_parameters({"close_contact_tol": 20})
    assert (
        prun.get_supervised_parameters()["close_contact_tol"]
        == 20
    )


@settings(deadline=None)
@given(
    w=st.integers(min_value=300, max_value=500),
    h=st.integers(min_value=300, max_value=500),
)
def test_frame_corners(w, h):
    assert len(deepof.annotation_utils.frame_corners(w, h)) == 4
    assert (
        deepof.annotation_utils.frame_corners(w, h, {"downright": "test"})["downright"]
        == "test"
    )

