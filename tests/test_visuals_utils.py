# @author NoCreativeIdeaForGoodUserName
# encoding: utf-8
# module deepof

"""

Testing module for deepof.visuals_utils

"""

import os

import numpy as np
import pandas as pd
from hypothesis import given
from hypothesis import settings, example
from hypothesis import strategies as st
from hypothesis import reproduce_failure
from hypothesis.extra.pandas import range_indexes, columns, data_frames
from shutil import rmtree
import warnings

from deepof.data import TableDict
from deepof.utils import connect_mouse
from deepof.visuals_utils import (
    time_to_seconds,
    seconds_to_time,
    calculate_average_arena,
    _filter_embeddings,
    _get_polygon_coords,
    _process_animation_data,
    create_bin_pairs,
    cohend,
    _preprocess_time_bins,
)

# TESTING SOME AUXILIARY FUNCTIONS #


@given(
    second=st.floats(min_value=0, max_value=100000),
    full_second=st.integers(min_value=0, max_value=100000),
)
def test_time_conversion(second, full_second):
    assert full_second == time_to_seconds(seconds_to_time(float(full_second)))
    second = np.round(second * 10**9) / 10**9 #up to 9 digits allowed
    second_second=time_to_seconds(seconds_to_time(float(second), cut_milliseconds=False)) 
    assert second == second_second #this pun is intended and necessary


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
    all_vertices

    all_vertices_dict={}
    for index, element in enumerate(all_vertices):
        all_vertices_dict[index] = element

    max_length = max(len(lst) for lst in all_vertices_dict.values()) + 1
    if num_points > max_length:
        avg_arena = calculate_average_arena(all_vertices_dict, num_points)
        assert len(avg_arena) == num_points



@given(
    keys=st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10),
        min_size=1, max_size=10, unique=True), 
    exp_condition=st.one_of(st.just('Cond1'),st.just('Cond2')) 
)
def test_filter_embeddings(keys,exp_condition):
    

    class Pseudo_Coordinates:
        def __init__(self, keys):
            self._exp_conditions = {}
 
            #create random exp conditions
            for i, key in enumerate(keys):
                if (i+1)%2==0:
                    self._exp_conditions[key]=pd.DataFrame([['even','blubb']],columns=['Cond1','Cond2'])
                else:
                    self._exp_conditions[key]=pd.DataFrame([['odd','blobb']],columns=['Cond1','Cond2'])

        @property
        def get_exp_conditions(self):
            """Return the stored dictionary with experimental conditions per subject."""
            return self._exp_conditions
    
    coordinates=Pseudo_Coordinates(keys)

    # Define a test embedding dictionary
    embeddings = {i: np.random.normal(size=(100, 10)) for i in keys}
    soft_counts = {}
    for i in keys:
        counts = np.abs(np.random.normal(size=(100, 2)))
        soft_counts[i] = counts / counts.sum(axis=1)[:, None]
    supervised_annotations= TableDict({i: pd.DataFrame(embeddings[i]) for i in keys}, typ='supervised')

    embeddings, soft_counts, supervised_annotations, concat_hue = _filter_embeddings(
    coordinates,
    embeddings,
    soft_counts,
    supervised_annotations,
    exp_condition,
    )

    N_keys=len(embeddings.keys())
    if exp_condition=='Cond1':
        comp_list=['odd' if i % 2 == 0 else 'even' for i in range(N_keys)]
        assert concat_hue == comp_list
    else:
        comp_list=['blobb' if i % 2 == 0 else 'blubb' for i in range(N_keys)]
        assert concat_hue == comp_list
    assert embeddings.keys()==soft_counts.keys()
    assert embeddings.keys()==supervised_annotations.keys()


@given(
    template=st.one_of(st.just("deepof_14"),st.just("deepof_11")), #deepof_8 does not have all required body parts
    animal_id=st.one_of(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20), st.just(None)),
)
def test_get_polygon_coords(template,animal_id):
    
    # Get body parts and coords
    features=connect_mouse(template).nodes()
    features=[feature[10:] for feature in features]
    coordinates = ['x', 'y']

    # Create a MultiIndex for the columns
    multi_index_columns = pd.MultiIndex.from_product(
        [features, coordinates],
        names=['Feature', 'Coordinate']
    )

    # Generate random data and dataframe
    data = np.random.rand(len(features)*len(coordinates),len(features)*len(coordinates))
    df = pd.DataFrame(data, columns=multi_index_columns)
    
    #to include None-case in testing for that 1 line of extra coverage
    if animal_id is None:
        a_id=""
    else:
        a_id=animal_id+"_"

    # add animal ids
    df.columns = pd.MultiIndex.from_tuples(
        [(f"{a_id}{feature}", coordinate) for feature, coordinate in df.columns]
    )

    [head, body, tail]=_get_polygon_coords(df,animal_id)

    assert head.shape[1]==8
    assert body.shape[1]==12
    assert tail.shape[1]==4


@settings(max_examples=20, deadline=None)
@given(
    min_confidence=st.floats(min_value=0.0, max_value=0.5),
    min_bout_duration=st.integers(min_value=1, max_value=5),
    selected_cluster=st.integers(min_value=0, max_value=1),
)
def test_process_animation_data(min_confidence,min_bout_duration,selected_cluster):
    
    animal_id="test_"
    # Get body parts and coords
    features=connect_mouse("deepof_14").nodes()
    features=[feature[10:] for feature in features]
    coordinates = ['x', 'y']

    # Create a MultiIndex for the columns
    multi_index_columns = pd.MultiIndex.from_product(
        [features, coordinates],
        names=['Feature', 'Coordinate']
    )

    # Generate random data and dataframe
    data = np.random.rand(len(features)*len(coordinates),len(features)*len(coordinates))
    coords = pd.DataFrame(data, columns=multi_index_columns)
    

    # add animal ids
    coords.columns = pd.MultiIndex.from_tuples(
        [(f"{animal_id}{feature}", coordinate) for feature, coordinate in coords.columns]
    )

    #create random embeddings and soft counts
    cur_embeddings = np.random.normal(size=(len(features)*len(coordinates)-5, 10))
    counts = np.abs(np.random.normal(size=(len(features)*len(coordinates)-5, 2)))
    cur_soft_counts = counts / counts.sum(axis=1)[:, None]

    
    (   
        coords,
        cur_embeddings,
        cluster_embedding,
        concat_embedding,
        hard_counts,
    ) = _process_animation_data(
        coords,
        cur_embeddings=cur_embeddings,
        cur_soft_counts=cur_soft_counts,
        min_confidence=min_confidence,
        min_bout_duration=min_bout_duration,
        selected_cluster=selected_cluster
    )

    assert coords.shape[0]==np.sum(hard_counts==selected_cluster) #data from correct cluster was selected for coords
    assert cur_embeddings[0].shape[0]>=concat_embedding.shape[0] #concatenated embeddings are of equal size or smaller than original
    assert cur_embeddings[0].shape[1]==concat_embedding.shape[1] #embeddings were reshaped to 2D
    assert cluster_embedding[0].shape[0]==coords.shape[0]  #data from correct cluster was selected for cluster_embedding


@given(
    L_array=st.integers(min_value=1, max_value=100000),
    N_time_bins=st.integers(min_value=1, max_value=100),
)
def test_create_bin_pairs(L_array, N_time_bins):
    assert all(np.diff(create_bin_pairs(L_array, N_time_bins)) >= 0)


@given(
    array_a=st.lists(
        elements=st.floats(min_value=-10e10, max_value=-0.00001), min_size=5, max_size=500
    ),
    array_b=st.lists(
        elements=st.floats(min_value=-10e10, max_value=-0.00001), min_size=5, max_size=500
    ),
    array_c=st.lists(
        elements=st.floats(min_value=0.00001, max_value=10e10), min_size=5, max_size=500
    ),
    array_d=st.lists(
        elements=st.floats(min_value=0.00001, max_value=10e10), min_size=5, max_size=500
    ),
)
def test_cohend(array_a, array_b, array_c, array_d):
    # tests for symmetry, scaling and constant invariance of cohends d
    assert (
        cohend(np.array(array_a) * 2, np.array(array_b) * 2)
        + cohend(np.array(array_b) + 1, np.array(array_a) + 1)
        < 10e-5
    )
    assert (
        cohend(np.array(array_a) * 2, np.array(array_c) * 2)
        + cohend(np.array(array_c) + 1, np.array(array_a) + 1)
        < 10e-5
    )
    assert (
        cohend(np.array(array_c) * 2, np.array(array_d) * 2)
        + cohend(np.array(array_d) + 1, np.array(array_c) + 1)
        < 10e-5
    )


# define pseudo coordinates object only containing properties necessary for testing bin preprocessing
class Pseudo_Coordinates:
    def __init__(self, start_times_raw, frame_rate):
        self._frame_rate = frame_rate
        self._start_times = {}
        self._table_lengths = {}  
        
        # set start time as time strings
        for i, start_time in enumerate(start_times_raw):
            start_time = seconds_to_time(start_time)
            self._start_times[f"key{i + 1}"] = start_time

        # set lengths as a minimum of start time + 10 seconds
        for i, start_time in enumerate(start_times_raw):
            min_length = 120 * frame_rate
            self._table_lengths[f"key{i + 1}"] = int(min_length)


    def add_table_lengths(self, lengths):
        """Add multiple table lengths with keys 'key1', 'key2', etc."""
        for i, length in enumerate(lengths):
            self._table_lengths[f"key{i + 1}"] = int(length)

    def get_start_times(self):
        return self._start_times

    def get_table_lengths(self):
        return self._table_lengths


@settings(deadline=None, max_examples=100)    
@given(
    start_times_raw=st.lists(
        elements=st.integers(min_value=0, max_value=120), min_size=5, max_size=50
    ),
    frame_rate=st.floats(min_value=1, max_value=60),
    bin_size=st.floats(min_value=1, max_value=120),
    bin_index=st.floats(min_value=0, max_value=100),
    is_int=st.booleans(),
    has_precomputed_bins=st.booleans(),
    samples_max=st.integers(min_value=10, max_value=2000),
    makes_sense=st.one_of(
        st.just("yes"),
        st.just("no"),
        st.just("no bins")
    )
)
def test_preprocess_time_bins(
    start_times_raw, frame_rate, bin_size, bin_index, is_int, has_precomputed_bins, samples_max, makes_sense
    ):
    
    # Only allow up to 8 decimales for float inputs 
    # (because of time string conversion limitations this otherwise leads to 1-index deviations 
    # in requested and required result, causing the test to fail)
    bin_size=np.round(bin_size, decimals=8)
    bin_index=np.round(bin_index, decimals=8)

    # Create Pseudo_Coordinates
    coords = Pseudo_Coordinates(start_times_raw,frame_rate)
    precomputed_bins=None

    # Simulate precomputed bin input 
    # (_preprocess_time_bins just skips them, so I don't know why I put the effort in that)
    if has_precomputed_bins:
        precomputed_bins=np.array([False]*int((bin_index+bin_size)*frame_rate+10))
        start=int(bin_index*frame_rate)
        stop=start+int(bin_size*frame_rate)
        precomputed_bins[start:stop]=True

    # Simulate index and time string user inputs
    if is_int:
        bin_size_user = int(bin_size)
        max_bin_no=(120*frame_rate)/np.round(bin_size_user*frame_rate)-1
        bin_index_user = int(np.min([int(bin_index),np.max([0,max_bin_no])]))
    else:
        bin_index_user = seconds_to_time(bin_index, False)
        bin_size_user = seconds_to_time(bin_size, False)

    # Simulate "special" inputs"
    if makes_sense=="no":
        bin_index_user="Banana!"
    elif makes_sense=="no bins":
        bin_size_user=None
        bin_index_user=None
        precomputed_bins=None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bin_info = _preprocess_time_bins(
        coordinates=coords, bin_size=bin_size_user, bin_index=bin_index_user, precomputed_bins=precomputed_bins, samples_max=samples_max,
        )

    for key in bin_info.keys():
        lengths=coords.get_table_lengths()
        assert isinstance(bin_info[key], np.ndarray)
        if (len(bin_info[key])>0):
            assert bin_info[key][-1] <= lengths[key]
            assert bin_info[key][0] >= 0
    