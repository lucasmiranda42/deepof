# @author NoCreativeIdeaForGoodUserName
# encoding: utf-8
# module deepof

"""

Testing module for deepof.visuals

"""

import os
from itertools import combinations

import networkx as nx
import numpy as np
import pandas as pd
from hypothesis import HealthCheck
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis import reproduce_failure
from hypothesis.extra.numpy import arrays
from hypothesis.extra.pandas import range_indexes, columns, data_frames
from scipy.spatial import distance
from shutil import rmtree

import deepof.data
from deepof.visuals_utils import (
    calculate_average_arena,
    time_to_seconds,
    seconds_to_time,
)

# TESTING SOME AUXILIARY FUNCTIONS #


@settings(deadline=None)
@given(
    all_vertices=st.lists(
        st.lists(
            st.tuples(
                st.floats(min_value=0, max_value=1000),
                st.floats(min_value=0, max_value=1000),
            ),
            min_size=1,
            max_size=10,
        ),
        min_size=1,
        max_size=10,
    ),
    num_points=st.integers(min_value=1, max_value=10000),
)
def test_calculate_average_arena(all_vertices, num_points):
    max_length = max(len(lst) for lst in all_vertices) + 1
    if num_points > max_length:
        avg_arena = calculate_average_arena(all_vertices, num_points)
        assert len(avg_arena) == num_points


@given(
    second=st.floats(min_value=0, max_value=100000),
    full_second=st.integers(min_value=0, max_value=100000),
)
def test_time_conversion(second, full_second):
    assert full_second == time_to_seconds(seconds_to_time(float(full_second)))
    second = np.round(second * 10**9) / 10**9
    assert second == time_to_seconds(seconds_to_time(second, False))
