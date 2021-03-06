# @author lucasmiranda42
# encoding: utf-8
# module deepof

"""

Testing module for deepof.models

"""

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import deepof.models
import deepof.model_utils
import tensorflow as tf

tf.config.experimental_run_functions_eagerly(True)


@settings(deadline=None, max_examples=10)
@given(
    loss=st.one_of(st.just("ELBO"), st.just("MMD"), st.just("ELBO+MMD")),
    kl_warmup_epochs=st.integers(min_value=0, max_value=5),
    mmd_warmup_epochs=st.integers(min_value=0, max_value=5),
    montecarlo_kl=st.integers(min_value=1, max_value=10),
    number_of_components=st.integers(min_value=1, max_value=5),
)
def test_GMVAE_build(
    loss,
    kl_warmup_epochs,
    mmd_warmup_epochs,
    montecarlo_kl,
    number_of_components,
):
    deepof.models.GMVAE(
        loss=loss,
        kl_warmup_epochs=kl_warmup_epochs,
        mmd_warmup_epochs=mmd_warmup_epochs,
        montecarlo_kl=montecarlo_kl,
        number_of_components=number_of_components,
        next_sequence_prediction=True,
        phenotype_prediction=True,
        rule_based_prediction=True,
        overlap_loss=True,
    ).build(
        input_shape=(
            100,
            15,
            10,
        )
    )
